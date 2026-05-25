#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SearchRunner 门面测试。"""

import unittest
from unittest.mock import patch

from calculation.search.run.runner import SearchRunner


class TestSearchRunner(unittest.TestCase):
    @patch("calculation.search.run.runner.run_search_session")
    def test_run_delegates_to_session(self, mock_run) -> None:
        mock_run.return_value = object()
        result = SearchRunner.run(
            base_context=object(),
            weapons=[],
            equipment_catalog={},
            config=object(),
        )
        self.assertIs(result, mock_run.return_value)
        mock_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
