# PyInstaller runtime hook — runs before main.py inside the frozen app.
#
# Every module finds its data folder as Path(sys.executable).parent and writes
# config, memory and certs there. In an installed app that folder is the
# program itself (a signed macOS bundle, Program Files on Windows), which must
# never be written to. So the app's home moves to the per-user data folder of
# each OS: seeded from the bundle on every launch (shipped code refreshed, user
# files never overwritten) and pointed at by sys.executable, which is all the
# existing get_base_dir() helpers look at.
import os
import shutil
import sys
from pathlib import Path


def _user_home() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "ARVIN"
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming") / "ARVIN"
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "ARVIN"


if getattr(sys, "frozen", False):
    _home = _user_home()
    _seed = Path(sys._MEIPASS) / "seed"

    # Shipped with the app: always replaced so an update takes effect.
    _ALWAYS = {"actions", "core"}

    for _src in _seed.rglob("*"):
        if _src.is_dir():
            continue
        _rel = _src.relative_to(_seed)
        _dst = _home / _rel
        if _dst.exists() and _rel.parts[0] not in _ALWAYS:
            continue   # the user's config, memory or plugins — leave alone
        _dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_src, _dst)

    (_home / "memory").mkdir(parents=True, exist_ok=True)
    sys.executable = str(_home / Path(sys.executable).name)
