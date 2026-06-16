#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""

避免 ``platform`` 经 WMI 查询卡死（Windows）。



某些库（如 PyInstaller.compat）在导入时会调用

``platform.release()`` / ``platform.win32_ver()`` 等；部分机器上 WMI 会无限阻塞，

表现为 ``main.py`` / ``build.py`` 启动后长时间无响应。



在可能触发 WMI 的导入前调用 ``apply_platform_win32_patch()``。

"""

from __future__ import annotations

import os
import sys
from collections.abc import Callable


def _read_windows_version_from_registry() -> tuple[str, str, str]:
    """返回 (release 主版本, version 点分串, machine)。"""

    import winreg

    cvkey = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"

    with winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, cvkey) as key:
        build = int(winreg.QueryValueEx(key, "CurrentBuildNumber")[0])

        try:
            major = int(winreg.QueryValueEx(key, "CurrentMajorVersionNumber")[0])

            minor = int(winreg.QueryValueEx(key, "CurrentMinorVersionNumber")[0])

        except OSError:
            major = 11 if build >= 22000 else 10

            minor = 0

    release = "11" if build >= 22000 else str(major)

    version = f"{major}.{minor}.{build}"

    machine = os.environ.get("PROCESSOR_ARCHITEW6432") or os.environ.get("PROCESSOR_ARCHITECTURE") or "AMD64"

    return release, version, machine


def apply_platform_win32_patch() -> None:
    """在导入 GUI / PyInstaller 之前调用，替换会触发 WMI 的 ``platform`` 接口。"""

    if sys.platform != "win32":
        return

    import platform

    if getattr(platform.win32_ver, "_edc_no_wmi_patch", False):
        return

    _orig_win32_ver: Callable[..., tuple[str, str, str, str]] = platform.win32_ver

    def _win32_ver_via_registry(
        release: str = "",
        version: str = "",
        csd: str = "",
        ptype: str = "",
    ) -> tuple[str, str, str, str]:
        try:
            rel, ver, _machine = _read_windows_version_from_registry()

            return (rel, version or ver, csd, ptype or "Multiprocessor Free")

        except OSError:
            return _orig_win32_ver(release, version, csd, ptype)

    def _uname_no_wmi() -> platform.uname_result:
        try:
            rel, ver, machine = _read_windows_version_from_registry()

        except OSError:
            rel, ver, machine = "10", "10.0.0", _windows_machine_from_env()

        return platform.uname_result(
            system="Windows",
            node=os.environ.get("COMPUTERNAME", "localhost"),
            release=rel,
            version=ver,
            machine=machine,
        )

    def _system_no_wmi() -> str:
        return "Windows"

    def _machine_no_wmi() -> str:
        return _windows_machine_from_env()

    def _release_no_wmi() -> str:
        return _uname_no_wmi().release

    def _version_no_wmi() -> str:
        return _uname_no_wmi().version

    _win32_ver_via_registry._edc_no_wmi_patch = True  # type: ignore[attr-defined]

    _uname_no_wmi._edc_no_wmi_patch = True  # type: ignore[attr-defined]

    _system_no_wmi._edc_no_wmi_patch = True  # type: ignore[attr-defined]

    _machine_no_wmi._edc_no_wmi_patch = True  # type: ignore[attr-defined]

    _release_no_wmi._edc_no_wmi_patch = True  # type: ignore[attr-defined]

    _version_no_wmi._edc_no_wmi_patch = True  # type: ignore[attr-defined]

    platform.win32_ver = _win32_ver_via_registry  # type: ignore[assignment]

    platform.uname = _uname_no_wmi  # type: ignore[assignment]

    platform.system = _system_no_wmi  # type: ignore[assignment]

    platform.machine = _machine_no_wmi  # type: ignore[assignment]

    platform.release = _release_no_wmi  # type: ignore[assignment]

    platform.version = _version_no_wmi  # type: ignore[assignment]


def _windows_machine_from_env() -> str:
    return os.environ.get("PROCESSOR_ARCHITEW6432") or os.environ.get("PROCESSOR_ARCHITECTURE") or "AMD64"


def get_physical_processor_count(*, logical_fallback: int = 1) -> int:
    """通过 kernel32 统计物理核心数（不启动子进程、不访问 WMI）。

    失败时返回 ``logical_fallback``（调用方通常传入 ``os.cpu_count()``）。
    """
    if sys.platform != "win32":
        return max(1, logical_fallback)

    from ctypes import POINTER, Structure, Union, WinDLL, byref, c_int, c_size_t, c_ulonglong, get_last_error, sizeof
    from ctypes import wintypes as w

    relation_processor_core = 0
    ulong_ptr = c_size_t
    ulonglong = c_ulonglong

    class _ProcessorCore(Structure):
        _fields_ = (("Flags", w.BYTE),)

    class _NumaNode(Structure):
        _fields_ = (("NodeNumber", w.DWORD),)

    class _CacheDescriptor(Structure):
        _fields_ = (
            ("Level", w.BYTE),
            ("Associativity", w.BYTE),
            ("LineSize", w.WORD),
            ("Size", w.DWORD),
            ("Type", c_int),
        )

    class _ProcessorInfoUnion(Union):
        _fields_ = (
            ("ProcessorCore", _ProcessorCore),
            ("NumaNode", _NumaNode),
            ("Cache", _CacheDescriptor),
            ("Reserved", ulonglong * 2),
        )

    class _SystemLogicalProcessorInformation(Structure):
        _anonymous_ = ("Anonymous",)
        _fields_ = (
            ("ProcessorMask", ulong_ptr),
            ("Relationship", c_int),
            ("Anonymous", _ProcessorInfoUnion),
        )

    kernel32 = WinDLL("kernel32", use_last_error=True)
    kernel32.GetLogicalProcessorInformation.argtypes = (
        POINTER(_SystemLogicalProcessorInformation),
        w.LPDWORD,
    )
    kernel32.GetLogicalProcessorInformation.restype = w.BOOL

    buf_len = w.DWORD(0)
    entry_size = sizeof(_SystemLogicalProcessorInformation)
    kernel32.GetLogicalProcessorInformation(None, byref(buf_len))
    if buf_len.value == 0:
        return max(1, logical_fallback)

    count = buf_len.value // entry_size
    buffer = (_SystemLogicalProcessorInformation * count)()
    if not kernel32.GetLogicalProcessorInformation(buffer, byref(buf_len)):
        if get_last_error() != 0:
            return max(1, logical_fallback)

    physical = sum(1 for entry in buffer if entry.Relationship == relation_processor_core)
    if physical <= 0:
        return max(1, logical_fallback)
    return physical
