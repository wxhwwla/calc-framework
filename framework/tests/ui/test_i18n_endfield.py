# SPDX-License-Identifier: AGPL-3.0
"""终末地桌面计算页 i18n 键测试。"""

from __future__ import annotations

import pytest

from calc_framework.ui.i18n import DesktopTranslator, set_locale, tr

_ENDFIELD_KEYS = (
    "desktop.endfield.hintLoadZones",
    "desktop.endfield.confirmSelection",
    "desktop.endfield.goAdvanced",
    "desktop.endfield.tabCalc",
    "desktop.endfield.tabAdvanced",
    "desktop.endfield.confirmPending",
    "desktop.endfield.pendingConfirm",
    "desktop.endfield.computing",
    "desktop.endfield.confirmed",
    "desktop.endfield.totalSettlement",
    "desktop.endfield.totalEmptyHint",
    "desktop.endfield.segmentRow",
    "desktop.endfield.subtotal",
    "desktop.endfield.weightedTotal",
    "desktop.endfield.skillInfo",
    "desktop.endfield.genericRow",
    "desktop.endfield.dialogHistTitle",
    "desktop.endfield.dialogCompareTitle",
    "desktop.endfield.dialogDashboardTitle",
    "desktop.endfield.searchBrowserTitle",
    "desktop.endfield.searchBrowserEmpty",
    "desktop.endfield.ocrMainTitle",
    "desktop.endfield.ocrDownloadModel",
)


@pytest.fixture(autouse=True)
def _restore_locale() -> None:
    yield
    set_locale("zh-CN")


@pytest.mark.parametrize("key", _ENDFIELD_KEYS)
def test_endfield_keys_exist_in_zh_cn(key: str) -> None:
    set_locale("zh-CN")
    value = tr(key)
    assert value != key
    assert value


@pytest.mark.parametrize("key", _ENDFIELD_KEYS)
def test_endfield_keys_exist_in_en(key: str) -> None:
    set_locale("en")
    value = tr(key)
    assert value != key
    assert value


def test_endfield_segment_row_interpolation_en() -> None:
    set_locale("en")
    text = tr(
        "desktop.endfield.segmentRow",
        index="1",
        single="100.0",
        count=3,
        total="300.0",
        share=" (10.0%)",
    )
    assert "Segment 1" in text
    assert "100.0" in text
    assert "300.0" in text


def test_endfield_weighted_total_zh() -> None:
    set_locale("zh-CN")
    text = tr("desktop.endfield.weightedTotal", total="12,345.6")
    assert "加权总伤" in text
    assert "12,345.6" in text


def test_isolated_translator_endfield_confirm() -> None:
    t = DesktopTranslator()
    t.set_locale("en")
    assert t.tr("desktop.endfield.confirmSelection") == "Confirm Selection"
