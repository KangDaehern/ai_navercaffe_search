from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE_DIR = ROOT / ".browser-profile"
READY_MARKER = PROFILE_DIR / ".ready"
OUTPUT_DIR = ROOT / "output"
ARTIFACTS_DIR = ROOT / "artifacts"
