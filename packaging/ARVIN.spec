# PyInstaller spec for Windows, macOS and Linux.  Build from the repo root, on
# the OS you are building for (PyInstaller does not cross-compile):
#     pyinstaller --noconfirm packaging/ARVIN.spec
# Output: dist/ARVIN.app on macOS, the dist/ARVIN/ folder elsewhere.
# .github/workflows/release.yml runs this on all three for every v* tag.
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH).parent

# actions/ and plugins/ are loaded from .py files on disk at runtime, so the
# sources ship as data (copied to Application Support by the runtime hook) AND
# as hidden imports, so PyInstaller bundles the libraries they import.
seed = [(str(p), "seed/actions") for p in (ROOT / "actions").glob("*.py")]
seed += [(str(p), "seed/plugins") for p in (ROOT / "plugins").glob("*.py")]
seed += [(str(ROOT / "core" / "prompt.txt"), "seed/core")]

datas = seed + [
    (str(ROOT / "core" / "face_model.obj"), "core"),
    (str(ROOT / "core" / "prompt.txt"), "core"),
    (str(ROOT / "dashboard" / "static"), "dashboard/static"),
]

# actions/ has no __init__.py, so collect_submodules() can't list it — name
# every module. No "config" data folder may ship either: it would shadow the
# config package for the action files.
hiddenimports = (
    [f"actions.{p.stem}" for p in (ROOT / "actions").glob("*.py")]
    + [f"plugins.{p.stem}" for p in (ROOT / "plugins").glob("*.py")]
    + ["config"]
    + collect_submodules("dashboard")
    + collect_submodules("uvicorn")
)

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    datas=datas,
    hiddenimports=hiddenimports,
    runtime_hooks=[str(Path(SPECPATH) / "rthook_appsupport.py")],
    # Windows-only libraries named in requirements.txt.
    excludes=[] if sys.platform == "win32" else
             ["comtypes", "pycaw", "pywin32", "pywinauto", "win10toast", "wmi"],
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="ARVIN",
    console=False,
    icon=str(ROOT / "config" / "ARVIN.ico") if sys.platform != "linux" else None,
)
coll = COLLECT(exe, a.binaries, a.datas, name="ARVIN")

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="ARVIN.app",
        icon=str(ROOT / "config" / "ARVIN.ico"),
        bundle_identifier="com.nishchay.arvin",
        info_plist={
            "CFBundleShortVersionString": "1.0.0",
            "NSHighResolutionCapable": True,
            # macOS shows these when asking for permission; without them the
            # request is refused silently.
            "NSMicrophoneUsageDescription": "ARVIN listens to your voice commands.",
            "NSCameraUsageDescription": "ARVIN can look through the camera when you ask it to.",
            "NSAppleEventsUsageDescription": "ARVIN controls other apps on your behalf.",
        },
    )
