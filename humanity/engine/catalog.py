"""One catalog shared by the Python engine and the HTML interface."""

import json
from importlib.resources import files

CATALOG = json.loads(files("humanity.data").joinpath("catalog.json").read_text(encoding="utf-8"))
LOCATIONS = CATALOG["locations"]
ACTION_LOCATIONS = CATALOG["actionLocations"]
FIRST_NAMES = CATALOG["firstNames"]
LAST_NAMES = CATALOG["lastNames"]
ROLES = CATALOG["roles"]
BACKGROUNDS = CATALOG["backgrounds"]
