"""Behavioral, compatibility, and persistence tests using only the stdlib."""

import json
import math
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from humanity import Simulation
from humanity.application import ApplicationController
from humanity.engine.events import emit
from humanity.engine.models import Event
from humanity.engine.perception import appraise, perceive
from humanity.engine.snapshots import loads, to_wire
from humanity.engine.systems import System

ROOT = Path(__file__).resolve().parents[1]


def normalize(value):
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items() if item is not None}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value


class EngineTests(unittest.TestCase):
    def test_determinism_and_resume(self):
        original = Simulation("repeatable", 24)
        original.step(18)
        original.set_condition("pressure", .8)
        restored = Simulation.from_snapshot(original.snapshot())
        for sim in (original, restored):
            sim.announce_achievement("person-3")
            sim.step(24)
        self.assertEqual(original.snapshot(), restored.snapshot())

    def test_emotion_is_separate_from_public_expression(self):
        sim = Simulation(population=3)
        subject, kind, competitive = sim.world.agents
        kind.traits.ambition = .1
        kind.needs.esteem = .9
        competitive.traits.ambition = .95
        competitive.traits.empathy = .7
        competitive.traits.sensitivity = .8
        competitive.traits.impression_management = .95
        competitive.traits.self_control = .9
        competitive.needs.esteem = .1
        event = Event("test-event", 0, "achievement", "پیشرفت یک نفر", "public", subject.id)
        first = appraise(kind, event, subject)
        second = appraise(competitive, event, subject)
        self.assertGreater(second.envy, first.envy)
        self.assertGreater(second.joy, 0)
        self.assertTrue(second.masked)
        perceive(sim.world, competitive, event)
        self.assertEqual(competitive.public_state.action, "celebrate")
        self.assertGreater(competitive.emotions.envy, 0)

    def test_history_changes_interpretation_and_relationships_are_directed(self):
        sim = Simulation(population=2)
        subject, observer = sim.world.agents
        observer.values.fairness = 1
        event = Event("success", 0, "achievement", "پیشرفت", "public", subject.id)
        observer.beliefs.fairness = .95
        first = appraise(observer, event, subject)
        observer.beliefs.fairness = .05
        second = appraise(observer, event, subject)
        self.assertGreater(second.suspicion, first.suspicion)
        reverse_before = subject.relationships[observer.id].trust
        perceive(sim.world, observer, Event("help", 0, "help", "کمک", "local", subject.id, observer.id))
        self.assertEqual(subject.relationships[observer.id].trust, reverse_before)

    def test_privacy_and_rejected_invitation(self):
        sim = Simulation(population=24)
        sim.step(8)
        self.assertTrue(all(not event.observers for event in sim.world.events if event.visibility == "private"))
        first, second = sim.world.agents[:2]
        event = Event("reject", 8, "rejection", "دعوت رد شد", "local", first.id, second.id)
        self.assertIsNone(perceive(sim.world, second, event))
        before = first.emotions.anxiety
        perceive(sim.world, first, event)
        self.assertGreater(first.emotions.anxiety, before)

    def test_extension_lifecycle_and_deferred_events_after_resume(self):
        def after(context):
            context.world.extensions["counter"] = context.world.extensions.get("counter", 0) + 1
            if context.world.tick == 1:
                context.emit(kind="achievement", text="رویداد افزونه", visibility="public", actor_id="person-1")
        system = System("counter", "after", after, order=20)
        sim = Simulation(population=3, systems=[system])
        sim.step()
        event_id = sim.world.pending_events[0].id
        with self.assertRaises(ValueError):
            Simulation.from_snapshot(sim.snapshot())
        restored = Simulation.from_snapshot(sim.snapshot(), systems=[system])
        restored.step()
        event = next(e for e in restored.world.events if e.id == event_id)
        self.assertTrue(event.observers)
        self.assertFalse(restored.world.pending_events)
        self.assertEqual(restored.world.extensions["counter"], 2)
        with self.assertRaises(ValueError):
            restored.register_system(system)

    def test_large_world_bounds(self):
        sim = Simulation("large", 240)
        sim.step(72)
        self.assertEqual(len({a.identity.name for a in sim.world.agents}), 240)
        for person in sim.world.agents:
            self.assertLessEqual(len(person.memories), 82)
            self.assertEqual(person.memories[0].source, "background")
            for state in (person.traits, person.needs, person.emotions, person.beliefs):
                self.assertTrue(all(0 <= v <= 1 for v in vars(state).values()))
        self.assertLessEqual(len(sim.world.events), 400)
        self.assertEqual(len(Simulation.from_snapshot(sim.snapshot()).world.agents), 240)

    def test_invalid_snapshots_and_controls(self):
        for text in ("{}", "null", "not JSON", '{"format":"humanity.sh","version":1,"world":null}'):
            with self.assertRaises((ValueError, TypeError)):
                loads(text)
        sim = Simulation(population=2)
        invalid = json.loads(sim.snapshot())
        invalid["world"]["agents"][0]["needs"]["energy"] = -1
        with self.assertRaises(ValueError):
            loads(json.dumps(invalid))
        invalid["world"]["agents"][0]["needs"]["energy"] = True
        with self.assertRaises(ValueError):
            loads(json.dumps(invalid))
        for value in (float("nan"), -1, True):
            with self.assertRaises(ValueError):
                sim.set_condition("pressure", value)
        with self.assertRaises(ValueError):
            sim.step(True)


@unittest.skipUnless(shutil.which("node"), "Node is only needed for cross-language migration tests")
class MigrationTests(unittest.TestCase):
    def reference(self, request):
        result = subprocess.run(["node", str(ROOT / "tests" / "reference-world.mjs")], input=json.dumps(request), text=True, capture_output=True, check=True, cwd=ROOT)
        return result.stdout

    def assert_worlds_equal(self, first, second):
        # Optional null fields can be absent in Python's compact representation.
        self.assertEqual(normalize(json.loads(first)), normalize(json.loads(second)))

    def test_identical_worlds_across_languages_and_unicode_seeds(self):
        for seed in ("hello-friend", "جامعه🌱"):
            with self.subTest(seed=seed):
                original = self.reference({"options": {"seed": seed, "population": 24}, "operations": [{"method": "step", "count": 24}]})
                python = Simulation(seed, 24)
                python.step(24)
                self.assert_worlds_equal(original, python.snapshot())

    def test_web_save_continues_in_python_and_python_save_continues_in_web(self):
        saved = self.reference({"options": {"seed": "old-world", "population": 24}, "operations": [{"method": "step", "count": 8}, {"method": "condition", "key": "socialSafety", "value": .2}]})
        python = Simulation.from_snapshot(saved)
        python.announce_achievement("person-3")
        python.step(8)
        expected = self.reference({"snapshot": saved, "operations": [{"method": "achievement", "id": "person-3"}, {"method": "step", "count": 8}]})
        self.assert_worlds_equal(expected, python.snapshot())
        exported = python.snapshot()
        python.step(4)
        continued = self.reference({"snapshot": exported, "operations": [{"method": "step", "count": 4}]})
        self.assert_worlds_equal(continued, python.snapshot())


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.controller = ApplicationController(Path(self.directory.name), fresh=True)

    def test_manual_save_load_and_session_are_separate(self):
        c = self.controller
        c.handle("save", {})
        c.handle("step", {})
        c.save_session()
        resumed = ApplicationController(c.data_dir)
        self.assertEqual(resumed.simulation.world.tick, 7)
        resumed.handle("load", {})
        self.assertEqual(resumed.simulation.world.tick, 6)

    def test_invalid_import_preserves_current_world(self):
        before = self.controller.simulation.snapshot()
        with self.assertRaises(ValueError):
            self.controller.handle("import", {"text": "{}"})
        self.assertEqual(before, self.controller.simulation.snapshot())

    def test_projection_never_loses_saved_memories(self):
        c = self.controller
        c.simulation.step(24)
        state = c.state()
        self.assertEqual(state["backend"], "python")
        projected_count = len(state["world"]["agents"][1]["memories"])
        self.assertLess(projected_count, len(c.simulation.world.agents[1].memories))
        c.handle("inspect", {"id": "person-2"})
        self.assertEqual(len(c.state()["world"]["agents"][1]["memories"]), len(c.simulation.world.agents[1].memories))
        with self.assertRaises(ValueError):
            Simulation.from_snapshot(json.dumps({"format": "humanity.sh", "version": 1, "world": state["world"]}))
        c.handle("save", {})
        restored = Simulation.from_snapshot((c.data_dir / "world.json").read_text())
        self.assertEqual(len(restored.world.agents[1].memories), len(c.simulation.world.agents[1].memories))

    def test_announcements_keep_observers_memories_in_projection(self):
        result = self.controller.handle("achievement", {"id": "person-1"})["state"]
        event = next(e for e in result["world"]["events"] if e["id"] == result["experimentId"])
        for observer_id in event["observers"]:
            person = next(a for a in result["world"]["agents"] if a["id"] == observer_id)
            self.assertTrue(any(m.get("eventId") == event["id"] for m in person["memories"]))

    def test_unreadable_session_is_preserved(self):
        path = self.controller.data_dir / "session.json"
        path.write_text("broken old session")
        next_controller = ApplicationController(self.controller.data_dir)
        next_controller.save_session()
        backups = list(self.controller.data_dir.glob("session-unreadable-*.json"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "broken old session")
