#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""向后兼容重导出。CalcWorker 已移至 ``utils.gui.qt_worker``。"""

from utils.gui.qt_worker import CalcWorker  # noqa: F401  # type: ignore[unused-import]
