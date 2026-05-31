#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""数据录入 ETL 工具入口。

用法::

    python -m tools.data_pipeline input.csv -o output.json
    python -m tools.data_pipeline characters.json --migrate-characters -o characters_standard.json
    python -m tools.data_pipeline data.json --validate
    python -m tools.data_pipeline --schema-help
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.data_pipeline.cli import main

if __name__ == "__main__":
    main()
