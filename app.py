from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent

sys.path.insert(
    0,
    str(ROOT_DIR / "backend")
)

from app.main import app