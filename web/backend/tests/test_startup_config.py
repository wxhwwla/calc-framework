# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""R-17 启动配置自检回归测试。

覆盖 ``CALC_API_KEY_PEPPER`` / ``CALC_ADMIN_TOKEN`` 的缺失、短值与合法值行为，
并验证 ``web.backend.main`` 在 pepper 显式配置但过短时导入即失败（启动自检）。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_BACKEND = _REPO / "web" / "backend"
for _p in (str(_REPO / "framework" / "src"), str(_REPO), str(_BACKEND)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from api.internal.startup_config import (
    ADMIN_TOKEN_ENV,
    API_KEY_PEPPER_ENV,
    check_startup_config,
    run_startup_config_checks,
)

_VALID_PEPPER = "p" * 32


class TestCheckStartupConfig:
    def test_empty_env_warns_but_does_not_error(self) -> None:
        report = check_startup_config({})

        assert report.errors == ()
        assert report.saas_enabled is False
        joined = "\n".join(report.warnings)
        assert API_KEY_PEPPER_ENV in joined
        assert ADMIN_TOKEN_ENV in joined
        assert "匿名计算不受影响" in joined

    def test_short_pepper_is_fatal_error(self) -> None:
        report = check_startup_config({API_KEY_PEPPER_ENV: "too-short"})

        assert report.saas_enabled is False
        assert any(API_KEY_PEPPER_ENV in error and "32" in error for error in report.errors)

    def test_valid_pepper_enables_saas_without_warnings(self) -> None:
        report = check_startup_config({API_KEY_PEPPER_ENV: _VALID_PEPPER, ADMIN_TOKEN_ENV: "admin-token-16chr"})

        assert report.errors == ()
        assert report.warnings == ()
        assert report.saas_enabled is True

    def test_whitespace_only_pepper_is_treated_as_missing(self) -> None:
        report = check_startup_config({API_KEY_PEPPER_ENV: "   "})

        assert report.errors == ()
        assert report.saas_enabled is False


class TestRunStartupConfigChecks:
    def test_short_pepper_raises_on_startup(self) -> None:
        with pytest.raises(RuntimeError, match="32"):
            run_startup_config_checks(
                {API_KEY_PEPPER_ENV: "too-short"},  # pragma: allowlist secret（测试用短值，非真实密钥）
            )

    def test_missing_pepper_does_not_block_startup(self) -> None:
        report = run_startup_config_checks({})

        assert report.saas_enabled is False


class TestMainWiring:
    def _import_main(self, env_overrides: dict[str, str | None]) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        for key, value in env_overrides.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
        # 与 uvicorn 的实际启动方式一致：工作目录为 web/backend，导入顶层 main
        return subprocess.run(
            [sys.executable, "-c", "import main"],
            cwd=str(_BACKEND),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )

    def test_import_main_fails_fast_on_short_pepper(self) -> None:
        proc = self._import_main({API_KEY_PEPPER_ENV: "too-short"})

        assert proc.returncode != 0
        assert API_KEY_PEPPER_ENV in proc.stderr
        assert "32" in proc.stderr

    def test_import_main_allows_missing_pepper(self) -> None:
        proc = self._import_main({API_KEY_PEPPER_ENV: None})

        assert proc.returncode == 0, proc.stderr
