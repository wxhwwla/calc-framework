#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""搜索失败回调须正确绑定异常文案（回归：except 变量被清除）。"""

import unittest


class TestSearchErrorBinding(unittest.TestCase):
    def test_nested_default_arg_preserves_exception_message(self):
        captured: list[str] = []

        def schedule_on_main(callback) -> None:
            callback()

        try:
            raise RuntimeError("sqlite disk I/O error")

        except Exception as exc:

            def _report_failure(error: BaseException = exc) -> None:
                captured.append(str(error))

            schedule_on_main(_report_failure)

        self.assertEqual(captured, ["sqlite disk I/O error"])


if __name__ == "__main__":
    unittest.main()
