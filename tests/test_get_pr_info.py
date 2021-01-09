import re
from textwrap import dedent
from unittest import mock
from unittest.mock import PropertyMock

import pytest
from get_pr_info import extract_target_section, get_pr_number_from_commit_message, get_pr_summary
from github import BadCredentialsException, UnknownObjectException


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


class TestGetPrInfo:
    @pytest.fixture(autouse=True)
    def setUp(self):
        mock_client = mock.Mock()
        mock_repo = mock.Mock()
        mock_pull = mock.Mock()
        with mock.patch("get_pr_info.Github") as mock_github:
            mock_github.return_value = mock_client
            mock_client.get_repo.return_value = mock_repo
            mock_repo.get_pull.return_value = mock_pull
            self.mock_github = mock_github
            self.mock_client = mock_client
            self.mock_repo = mock_repo
            self.mock_pull = mock_pull

            yield

    def test_nomal(self):
        mock_body = PropertyMock(return_value="PR_INFO")
        type(self.mock_pull).body = mock_body
        actual = get_pr_summary(999, "GITHUB_TOKEN", "REPOSITORY_NAME")
        expected = "PR_INFO"

        assert actual == expected
        self.mock_github.assert_called_once_with("GITHUB_TOKEN")
        self.mock_client.get_repo.assert_called_once_with("REPOSITORY_NAME")
        self.mock_repo.get_pull.assert_called_once_with(999)
        assert mock_body.call_count == 1

    def test_bad_credential(self):
        # トークンが誤っている場合
        # APIにアクセスしたくないため、モックで例外を投げている
        # ユニットテストとしては意味がないが、仕様記載の意味で記載しておく
        # NOTE: トークンが誤っている場合でもgithubインスタンスの生成時にはエラーとならず、GitHub操作をした際にエラーとなる
        self.mock_client.get_repo.side_effect = BadCredentialsException(
            401,
            data={
                "message": "Bad credentials",
                "documentation_url": "https://docs.github.com/rest",
            },
        )

        with pytest.raises(BadCredentialsException):
            get_pr_summary(999, "GITHUB_TOKEN", "REPOSITORY_NAME")

        self.mock_github.assert_called_once_with("GITHUB_TOKEN")
        self.mock_client.get_repo.assert_called_once_with("REPOSITORY_NAME")
        self.mock_repo.get_pull.assert_not_called()

    def test_not_exists_repository(self):
        # リポジトリが存在しない場合
        # APIにアクセスしたくないため、モックで例外を投げている
        # ユニットテストとしては意味がないが、仕様記載の意味で記載しておく
        self.mock_client.get_repo.side_effect = UnknownObjectException(
            404,
            data={
                "message": "Not Found",
                "documentation_url": "https://docs.github.com/rest/reference/repos#get-a-repository",
            },
        )

        with pytest.raises(UnknownObjectException):
            get_pr_summary(999, "GITHUB_TOKEN", "REPOSITORY_NAME")

        self.mock_github.assert_called_once_with("GITHUB_TOKEN")
        self.mock_client.get_repo.assert_called_once_with("REPOSITORY_NAME")
        self.mock_repo.get_pull.assert_not_called()

    def test_not_exists_pr_number(self):
        # PR番号が存在しない場合
        # APIにアクセスしたくないため、モックで例外を投げている
        # ユニットテストとしては意味がないが、仕様記載の意味で記載しておく
        self.mock_repo.get_pull.side_effect = UnknownObjectException(
            404,
            data={
                "message": "Not Found",
                "documentation_url": "https://docs.github.com/rest/reference/pulls#get-a-pull-request",
            },
        )

        with pytest.raises(UnknownObjectException):
            get_pr_summary(999, "GITHUB_TOKEN", "REPOSITORY_NAME")

        self.mock_github.assert_called_once_with("GITHUB_TOKEN")
        self.mock_client.get_repo.assert_called_once_with("REPOSITORY_NAME")
        self.mock_repo.get_pull.assert_called_once_with(999)


class TestGetIntegrationTestPoint:
    def test_nomal(self):
        summary = dedent(
            """\
            ## 概要

            - 現状（As is）
              - こうなんです
            - 理想（To be）
              - こうなりたい
            - 問題（Problem）
              - こまってる
            - 解決・やったこと（Action）
              - これをやった

            ## 結合テスト観点

            - 対応概要
              - こうやった
            - 観点
              - こういうこと1
                - 条件: こうしてほしい2
              - こういうこと2
                - 条件: こうしてほしい2
            - 担当
              - API yamap55
            """
        )

        actual = extract_target_section(summary, "## 結合テスト観点")
        expected = dedent(
            """\
            ## 結合テスト観点

            - 対応概要
              - こうやった
            - 観点
              - こういうこと1
                - 条件: こうしてほしい2
              - こういうこと2
                - 条件: こうしてほしい2
            - 担当
              - API yamap55"""
        )

        assert actual == expected

    def test_not_exists_target_section(self):
        summary = ""
        actual = extract_target_section(summary, "## 結合テスト観点")
        expected = ""

        assert actual == expected

    def test_another_section_at_the_end(self):
        # 対象行より後ろに別のセクションが存在する場合

        summary = dedent(
            """\
            ## 概要

            - 現状（As is）
              - こうなんです
            - 理想（To be）
              - こうなりたい
            - 問題（Problem）
              - こまってる
            - 解決・やったこと（Action）
              - これをやった

            ## 結合テスト観点

            - 対応概要
              - こうやった
            - 観点
              - こういうこと1
                - 条件: こうしてほしい2
              - こういうこと2
                - 条件: こうしてほしい2
            - 担当
              - API yamap55

            ## 対象外セクション

            - 対象外です
            """
        )

        actual = extract_target_section(summary, "## 結合テスト観点")
        expected = dedent(
            """\
            ## 結合テスト観点

            - 対応概要
              - こうやった
            - 観点
              - こういうこと1
                - 条件: こうしてほしい2
              - こういうこと2
                - 条件: こうしてほしい2
            - 担当
              - API yamap55
            """
        )

        assert actual == expected
