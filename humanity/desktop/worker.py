"""One QObject, one worker thread, one owner of the simulation and its clock."""

import json
import logging
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from humanity.application import ApplicationController

logger = logging.getLogger(__name__)


class SimulationWorker(QObject):
    reply = Signal(str)
    updated = Signal(str)
    failed = Signal(str)

    def __init__(self, data_dir: Path, fresh=False):
        super().__init__()
        self.data_dir = data_dir
        self.fresh = fresh
        self.controller = None
        self.timer = None

    @Slot()
    def initialize(self):
        # Construct the timer and state in their owning thread, not the GUI thread.
        self.controller = ApplicationController(self.data_dir, fresh=self.fresh)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.advance)

    def schedule(self):
        if self.timer is None:
            return
        self.timer.stop()
        if self.controller.running:
            self.timer.start(max(50, round(1200 / self.controller.speed)))

    @Slot(str)
    def execute(self, raw: str):
        packet_id = None
        try:
            if len(raw) > 32_000_000:
                raise ValueError("Command too large")
            packet = json.loads(raw)
            if not isinstance(packet, dict) or not isinstance(packet.get("args", {}), dict):
                raise ValueError("Invalid command packet")
            packet_id = packet.get("id")
            if self.controller is None:
                self.initialize()
            result = self.controller.handle(packet.get("method"), packet.get("args", {}))
            if packet.get("method") == "state":
                logger.info("Desktop interface connected to Python engine at tick %s", self.controller.simulation.world.tick)
            self.schedule()
            response = {"id": packet_id, "ok": True, "result": result}
        except (ValueError, TypeError, OSError, KeyError) as error:
            response = {"id": packet_id, "ok": False, "error": str(error)}
        except Exception:
            logger.exception("Unexpected simulation command failure")
            response = {"id": packet_id, "ok": False, "error": "خطایی در موتور رخ داد؛ گزارش برنامه را بررسی کن."}
        self.reply.emit(json.dumps(response, ensure_ascii=False, allow_nan=False))

    @Slot()
    def advance(self):
        try:
            self.controller.advance()
            self.updated.emit(json.dumps(self.controller.state(), ensure_ascii=False, allow_nan=False))
        except Exception:
            self.controller.running = False
            logger.exception("Simulation stopped after an unexpected tick failure")
            self.failed.emit("اجرای جهان با خطا متوقف شد؛ وضعیت فعلی حفظ شده است.")
        finally:
            self.schedule()

    @Slot()
    def shutdown(self):
        if self.timer:
            self.timer.stop()
        if self.controller:
            try:
                self.controller.save_session()
            except OSError:
                logger.exception("Could not save the current session")
