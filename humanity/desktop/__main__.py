import sys

try:
    from .app import main
except ModuleNotFoundError as error:
    if error.name and error.name.startswith("PySide6"):
        print('Desktop dependencies are missing. Run: python -m pip install -e ".[desktop]"', file=sys.stderr)
        raise SystemExit(1)
    raise

raise SystemExit(main())
