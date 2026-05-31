"""Web 鍚庣璺緞璁剧疆鈥斺€旈泦涓鐞嗘墍鏈?sys.path 閰嶇疆銆?""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FRAMEWORK_SRC = _REPO_ROOT / "framework" / "src"

for _p in [str(_FRAMEWORK_SRC), str(_REPO_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)
