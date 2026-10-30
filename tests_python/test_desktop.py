"""Qt worker/bridge integration without creating a GUI or faking user input."""

import importlib.util
import json
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from humanity.desktop.assets import AssetServer

HAS_QT = importlib.util.find_spec("PySide6") is not None


class AssetTests(unittest.TestCase):
    def test_assets_are_served_but_python_and_git_files_are_not(self):
        server = AssetServer()
        server.start()
        self.addCleanup(server.close)
        for path, mime in (("/", "text/html"), ("/src/main.js", "text/javascript"), ("/humanity/data/catalog.json", "application/json")):
            with urllib.request.urlopen(server.origin + path, timeout=3) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers.get_content_type(), mime)
        for path in ("/.git/config", "/humanity/engine/simulation.py", "/public/../.git/config"):
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(server.origin + path, timeout=3)
            self.assertEqual(caught.exception.code, 404)


@unittest.skipUnless(HAS_QT, "Install the desktop extra to run Qt integration tests")
class QtBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtCore import QCoreApplication
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        from PySide6.QtCore import QThread
        from PySide6.QtTest import QSignalSpy
        from humanity.desktop.bridge import EngineBridge
        from humanity.desktop.worker import SimulationWorker
        self.directory = tempfile.TemporaryDirectory()
        self.thread = QThread()
        self.worker = SimulationWorker(Path(self.directory.name), fresh=True)
        self.worker.moveToThread(self.thread)
        self.bridge = EngineBridge()
        self.thread.started.connect(self.worker.initialize)
        self.bridge.command_requested.connect(self.worker.execute)
        self.worker.reply.connect(self.bridge.reply)
        self.worker.updated.connect(self.bridge.updated)
        self.thread.finished.connect(self.worker.deleteLater)
        self.replies = QSignalSpy(self.bridge.reply)
        self.updates = QSignalSpy(self.bridge.updated)
        self.thread.start()

    def tearDown(self):
        from PySide6.QtCore import QMetaObject, Qt
        QMetaObject.invokeMethod(self.worker, "shutdown", Qt.ConnectionType.BlockingQueuedConnection)
        self.thread.quit()
        self.assertTrue(self.thread.wait(5000))
        self.directory.cleanup()

    def request(self, method, args=None):
        index = self.replies.count()
        self.bridge.request(json.dumps({"id": str(index), "method": method, "args": args or {}}))
        if self.replies.count() == index:
            self.wait_for(self.bridge.reply, self.replies, index)
        return json.loads(self.replies.at(index)[0])

    def wait_for(self, signal, spy, previous_count):
        from PySide6.QtCore import QEventLoop, QTimer
        loop = QEventLoop()
        guard = QTimer()
        guard.setSingleShot(True)
        guard.timeout.connect(loop.quit)
        signal.connect(loop.quit)
        guard.start(10000)
        # A normal Qt event loop releases Python's GIL for the worker. QSignalSpy
        # wait() can block a Python worker with some PySide builds.
        if spy.count() == previous_count:
            loop.exec()
        signal.disconnect(loop.quit)
        guard.stop()
        self.assertGreater(spy.count(), previous_count, "Python worker did not reply")

    def test_state_step_save_and_load_roundtrip_in_worker(self):
        result = self.request("state")
        self.assertTrue(result["ok"])
        self.assertEqual(result["result"]["state"]["backend"], "python")
        self.assertEqual(result["result"]["state"]["world"]["tick"], 6)
        self.request("save")
        self.assertEqual(self.request("step")["result"]["state"]["world"]["tick"], 7)
        self.assertEqual(self.request("load")["result"]["state"]["world"]["tick"], 6)
        self.assertEqual(self.worker.thread(), self.thread)

    def test_encounter_uses_python_model_through_bridge(self):
        result = self.request("encounter", {"kind": "insult", "actorId": "person-1", "targetId": "person-2"})
        self.assertTrue(result["ok"])
        state = result["result"]["state"]
        target = next(a for a in state["world"]["agents"] if a["id"] == "person-2")
        memory = next(m for m in target["memories"] if m.get("eventId") == state["experimentId"])
        self.assertGreater(memory["emotionsAfter"]["disgust"], memory["emotionsBefore"]["disgust"])
        self.assertFalse(state["running"])

    def test_clock_is_owned_by_python_and_pause_stops_it(self):
        self.request("speed", {"value": 8})
        self.request("run", {"value": True})
        self.wait_for(self.bridge.updated, self.updates, 0)
        update = json.loads(self.updates.at(0)[0])
        self.assertGreater(update["world"]["tick"], 6)
        result = self.request("run", {"value": False})
        self.assertFalse(result["result"]["state"]["running"])

    def test_bridge_rejects_arbitrary_file_paths_and_uses_native_choice(self):
        result = self.request("export_file", {"path": "/should-not-be-written.json"})
        self.assertFalse(result["ok"])
        chosen = Path(self.directory.name) / "chosen-world.json"
        with patch("humanity.desktop.bridge.QFileDialog.getSaveFileName", return_value=(str(chosen), "")):
            result = self.request("export", {"path": "/ignored-path.json"})
        self.assertTrue(result["ok"])
        self.assertTrue(chosen.is_file())
        self.assertEqual(json.loads(chosen.read_text())["format"], "humanity.sh")
