# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""明日方舟 DAG 适配器。"""

from __future__ import annotations

from .adapter import compute_snapshot_with_dag
from .loader import ArknightsContextLoader

__all__ = [
    "ArknightsContextLoader",
    "compute_snapshot_with_dag",
]
