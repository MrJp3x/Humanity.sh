"""Application commands and view projections, independent of Qt.

Only one worker calls this controller. JavaScript receives independent views.
File operations always use complete snapshots, never trimmed view projections.
"""

from pathlib import Path
from dataclasses import fields, replace
from time import time_ns
import json

from .engine.agents import mask_gap, wellbeing
from .engine.models import World
from .engine.simulation import Simulation
from .engine.snapshots import MAX_SNAPSHOT_BYTES, atomic_write, camel_case, to_wire
from .engine.systems import metrics


def project_world(world: World, selected_id: str, experiment_id: str | None):
    projected = {camel_case(f.name): to_wire(getattr(world, f.name)) for f in fields(world) if f.name != "agents"}
    projected["agents"] = []
    for agent in world.agents:
        visible = agent.memories
        if agent.id != selected_id:
            latest_appraisal = next((m for m in reversed(agent.memories) if m.kind == "appraisal"), None)
            visible_ids = {m.id for m in agent.memories[-1:]}
            if latest_appraisal:
                visible_ids.add(latest_appraisal.id)
            if experiment_id:
                visible_ids.update(m.id for m in agent.memories if m.event_id == experiment_id)
            visible = [m for m in agent.memories if m.id in visible_ids]
        view = to_wire(replace(agent, memories=visible))
        view["_view"] = {"wellbeing": wellbeing(agent), "maskGap": mask_gap(agent), "memoryCount": len(agent.memories)}
        projected["agents"].append(view)
    projected["_viewMetrics"] = to_wire(metrics(world))
    projected["_projection"] = True
    return projected


class ApplicationController:
    def __init__(self, data_dir: Path, *, fresh=False):
        self.data_dir = Path(data_dir)
        self.running = False
        self.speed = 1
        self.generation = 0
        self.experiment_id = None
        self.startup_note = None
        self.session_backup_reason = None
        session = self.data_dir / "session.json"
        if session.exists() and not fresh:
            try:
                self.simulation = self.read_world(session)
                self.startup_note = "جهان از آخرین نشست باز شد."
                if json.loads(session.read_text(encoding="utf-8")).get("version") == 1:
                    self.startup_note = "جهان قبلی به مدل پنج احساس منتقل شد؛ ادامهٔ زندگی با قواعد تازه است."
                    self.session_backup_reason = "before-model-upgrade"
            except (OSError, ValueError, TypeError):
                self.simulation = self.new_simulation()
                self.session_backup_reason = "unreadable"
                self.startup_note = "ذخیرهٔ نشست قابل بازکردن نبود؛ فایل قبلی حفظ شده است."
        else:
            self.simulation = self.new_simulation()
        self.selected_id = self.simulation.world.agents[0].id

    @staticmethod
    def new_simulation(seed="hello-friend", population=48):
        simulation = Simulation(seed, population)
        simulation.step(6)
        return simulation

    @staticmethod
    def read_world(path: Path):
        if path.stat().st_size >= MAX_SNAPSHOT_BYTES:
            raise ValueError("فایل جهان بزرگ‌تر از حد مجاز است.")
        return Simulation.from_snapshot(path.read_text(encoding="utf-8"))

    def state(self):
        return {"world": project_world(self.simulation.world, self.selected_id, self.experiment_id),
                "running": self.running, "speed": self.speed, "selectedId": self.selected_id,
                "generation": self.generation, "experimentId": self.experiment_id,
                "backend": "python", "startupNote": self.startup_note}

    def replace(self, simulation: Simulation):
        self.running = False
        self.simulation = simulation
        self.selected_id = simulation.world.agents[0].id
        self.experiment_id = None
        self.generation += 1

    def advance(self):
        if self.running:
            self.simulation.step()

    def handle(self, method: str, args: dict):
        message = None
        if method == "state":
            pass
        elif method == "new_world":
            self.replace(self.new_simulation(args.get("seed", "hello-friend"), args.get("population", 48)))
        elif method == "step":
            if self.running:
                raise ValueError("برای پیشروی گام‌به‌گام، ابتدا زمان را متوقف کن.")
            self.simulation.step()
        elif method == "run":
            if type(args.get("value")) is not bool:
                raise ValueError("Invalid running state")
            self.running = args["value"]
        elif method == "speed":
            if type(args.get("value")) is not int or args["value"] not in (1, 3, 8):
                raise ValueError("Invalid speed")
            self.speed = args["value"]
        elif method == "inspect":
            person_id = args.get("id")
            if not isinstance(person_id, str) or self.simulation.world.person(person_id) is None:
                raise ValueError("Agent not found")
            self.selected_id = person_id
        elif method == "condition":
            key = {"socialSafety": "social_safety"}.get(args.get("key"), args.get("key"))
            self.simulation.set_condition(key, args.get("value"))
        elif method == "achievement":
            event = self.simulation.announce_achievement(args.get("id"))
            self.running = False
            self.experiment_id = event.id
        elif method == "encounter":
            event = self.simulation.encounter(args.get("kind"), args.get("actorId"), args.get("targetId"))
            self.running = False
            self.experiment_id = event.id
        elif method == "snapshot":
            return {"snapshot": self.simulation.snapshot()}
        elif method == "import":
            self.replace(Simulation.from_snapshot(args.get("text")))
        elif method == "save":
            atomic_write(self.data_dir / "world.json", self.simulation.snapshot())
            message = "جهان روی این دستگاه ذخیره شد."
        elif method == "load":
            path = self.data_dir / "world.json"
            if not path.exists():
                raise ValueError("هنوز ذخیره‌ای روی این دستگاه وجود ندارد.")
            self.replace(self.read_world(path))
            message = "جهان به آخرین ذخیره بازگشت."
        elif method == "export_file":
            atomic_write(Path(args["path"]), self.simulation.snapshot())
            message = "فایل جهان ذخیره شد."
        elif method == "import_file":
            self.replace(self.read_world(Path(args["path"])))
            message = "جهان از فایل باز شد."
        else:
            raise ValueError("Unknown application command")
        return {"state": self.state(), "message": message}

    def save_session(self):
        self.running = False
        session = self.data_dir / "session.json"
        if self.session_backup_reason and session.exists():
            session.replace(self.data_dir / f"session-{self.session_backup_reason}-{time_ns()}.json")
            self.session_backup_reason = None
        atomic_write(session, self.simulation.snapshot())
