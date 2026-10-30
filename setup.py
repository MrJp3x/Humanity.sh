"""Include the existing HTML interface in distributable Python wheels."""

from pathlib import Path
from shutil import copy2, copytree

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildWithInterface(build_py):
    def run(self):
        super().run()
        root = Path(__file__).parent
        destination = Path(self.build_lib) / "humanity" / "web"
        destination.mkdir(parents=True, exist_ok=True)
        copy2(root / "index.html", destination / "index.html")
        for directory in ("src", "public"):
            copytree(root / directory, destination / directory, dirs_exist_ok=True)
        catalog = destination / "humanity" / "data"
        catalog.mkdir(parents=True, exist_ok=True)
        copy2(root / "humanity" / "data" / "catalog.json", catalog / "catalog.json")


setup(cmdclass={"build_py": BuildWithInterface})
