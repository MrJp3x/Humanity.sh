"""A deliberately narrow bridge; file dialogs stay on the GUI thread."""

import json

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QFileDialog

FRONTEND_METHODS = {"state", "new_world", "step", "run", "speed", "inspect", "condition", "achievement", "snapshot", "import", "save", "load", "export", "open"}


class EngineBridge(QObject):
    command_requested = Signal(str)
    reply = Signal(str)
    updated = Signal(str)
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog_parent = parent

    @Slot(str)
    def request(self, raw):
        packet_id = None
        try:
            if len(raw) > 32_000_000:
                raise ValueError("Command too large")
            packet = json.loads(raw)
            if not isinstance(packet, dict):
                raise ValueError("Invalid command")
            packet_id = packet.get("id")
            method = packet.get("method")
            if method not in FRONTEND_METHODS or not isinstance(packet.get("args", {}), dict):
                raise ValueError("Unknown application command")
            if method in ("export", "open"):
                if method == "export":
                    path, _ = QFileDialog.getSaveFileName(self.dialog_parent, "ذخیرهٔ فایل جهان", "humanity-world.json", "Humanity world (*.json)")
                    command = "export_file"
                else:
                    path, _ = QFileDialog.getOpenFileName(self.dialog_parent, "باز کردن جهان", "", "Humanity world (*.json)")
                    command = "import_file"
                if not path:
                    self.reply.emit(json.dumps({"id": packet_id, "ok": True, "result": {"cancelled": True}}))
                    return
                # Paths originate in a native chooser, never in arbitrary JavaScript arguments.
                packet = {"id": packet_id, "method": command, "args": {"path": path}}
            self.command_requested.emit(json.dumps(packet, ensure_ascii=False))
        except (ValueError, TypeError) as error:
            self.reply.emit(json.dumps({"id": packet_id, "ok": False, "error": str(error)}))
