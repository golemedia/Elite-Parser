# tests/conftest.py
# Ensure the project root is on sys.path so `import eliteparser` works from tests.
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
