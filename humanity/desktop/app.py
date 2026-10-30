"""PySide6 window, local HTML assets, and the Python simulation worker."""

import argparse
import logging
import sys
import signal
from pathlib import Path

from PySide6.QtCore import QFile, QIODevice, QMetaObject, QStandardPaths, QThread, QTimer, Qt, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineScript
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from .assets import AssetServer
from .bridge import EngineBridge
from .worker import SimulationWorker


class LocalPage(QWebEnginePage):
    def __init__(self, origin, parent):
        super().__init__(parent)
        self.origin = origin

    def acceptNavigationRequest(self, url, navigation_type, is_main_frame):
        if not is_main_frame:
            return True
        return url.toString() == "about:blank" or (url.scheme() == "http" and f"http://{url.host()}:{url.port()}" == self.origin)

    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        if level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel:
            logging.error("Frontend: %s (%s:%s)", message, source_id, line_number)


class MainWindow(QMainWindow):
    def __init__(self, data_dir: Path, *, fresh=False):
        super().__init__()
        self.setWindowTitle("Humanity.sh — رصدخانهٔ جامعه")
        self.resize(1380, 940)
        self.setMinimumSize(900, 640)
        self.assets = AssetServer()
        url = self.assets.start()
        self.setWindowIcon(QIcon(str(self.assets.root / "public" / "favicon.svg")))
        self.view = QWebEngineView(self)
        self.page = LocalPage(self.assets.origin, self.view)
        self.view.setPage(self.page)
        self.setCentralWidget(self.view)
        self.bridge = EngineBridge(self)
        self.channel = QWebChannel(self.page)
        self.channel.registerObject("engine", self.bridge)
        self.page.setWebChannel(self.channel)
        self.inject_webchannel()
        self.thread = QThread(self)
        self.thread.setObjectName("Humanity simulation")
        self.worker = SimulationWorker(data_dir, fresh=fresh)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.initialize)
        self.bridge.command_requested.connect(self.worker.execute)
        self.worker.reply.connect(self.bridge.reply)
        self.worker.updated.connect(self.bridge.updated)
        self.worker.failed.connect(self.bridge.failed)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.start()
        self.view.loadFinished.connect(self.page_loaded)
        self.view.setUrl(QUrl(url))

    def inject_webchannel(self):
        resource = QFile(":/qtwebchannel/qwebchannel.js")
        if not resource.open(QIODevice.OpenModeFlag.ReadOnly):
            raise RuntimeError("Qt WebChannel JavaScript resource is unavailable")
        script = QWebEngineScript()
        script.setName("Humanity Qt WebChannel")
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(False)
        script.setSourceCode(bytes(resource.readAll()).decode("utf-8"))
        self.page.scripts().insert(script)

    def page_loaded(self, successful):
        if not successful:
            QMessageBox.critical(self, "Humanity.sh", "پنل برنامه بارگذاری نشد. فایل‌های رابط و گزارش اجرا را بررسی کن.")

    def closeEvent(self, event):
        # Finish queued work and persist the session in its owning thread.
        QMetaObject.invokeMethod(self.worker, "shutdown", Qt.ConnectionType.BlockingQueuedConnection)
        self.thread.quit()
        self.thread.wait()
        self.assets.close()
        event.accept()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Humanity.sh desktop observatory")
    parser.add_argument("--fresh", action="store_true", help="Start a fresh session instead of restoring the previous one")
    parser.add_argument("--data-dir", type=Path, help="Override the local save directory")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    app = QApplication(sys.argv[:1])
    app.setApplicationName("Humanity.sh")
    app.setOrganizationName("Humanity.sh")
    data_dir = args.data_dir or Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    window = MainWindow(data_dir, fresh=args.fresh)
    window.show()
    signal.signal(signal.SIGINT, lambda *_: window.close())
    heartbeat = QTimer()
    heartbeat.timeout.connect(lambda: None)
    heartbeat.start(250)
    try:
        return app.exec()
    finally:
        if window.thread.isRunning():
            window.close()
