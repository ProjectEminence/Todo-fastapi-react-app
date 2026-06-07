"""
CodeValid pytest conftest — prepends the installable package root to sys.path
(monorepo-safe via CODEVALID_PACKAGE_ROOT).
"""
import os
import sys
from pathlib import Path

codevalid_dir = Path(__file__).resolve().parent
app_root = codevalid_dir.parent
rel = os.environ.get("CODEVALID_PACKAGE_ROOT", "").strip().lstrip("/")
package_root = app_root / rel if rel else app_root
pkg_str = str(package_root.resolve())
if pkg_str not in sys.path:
    sys.path.insert(0, pkg_str)