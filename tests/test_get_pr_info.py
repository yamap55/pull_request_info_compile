import re

import pytest
from get_pr_info import get_pr_number_from_commit_message


class TestGetPrNumberFromCommitMessage:
    @pytest.fixture(autouse=True)
    def setUp(self):
        self.pattern = re.compile(r"#(\d*)")

    def test_not_match(self):
        actual = get_pr_number_from_commit_message("abcdefg", self.pattern)
        expected = 0
        assert actual == expected

    def test_match(self):
        actual = get_pr_number_from_commit_message("ab#123cd", self.pattern)
        expected = 123
        assert actual == expected

    def test_multi_match(self):
        actual = get_pr_number_from_commit_message("ab#123cd#456ef", self.pattern)
        expected = 123
        assert actual == expected

    def test_second_line_match(self):
        # 2行目にPR番号が含まれている場合
        actual = get_pr_number_from_commit_message("abc\ncd#123ef", self.pattern)
        expected = 0
        assert actual == expected

    def test_blank_str(self):
        actual = get_pr_number_from_commit_message("", self.pattern)
        expected = 0
        assert actual == expected
