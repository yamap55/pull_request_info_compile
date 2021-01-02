import os
import re
from typing import Any

from github import Github

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
COMMIT_MESSAGE = os.environ["COMMIT_MESSAGE"]
GITHUB_REPOSITORY_NAME = os.environ["GITHUB_REPOSITORY_NAME"]
PR_NUMBER_PATTERN = re.compile(r"#(\d*)")


def log(message: Any, prefix: Any = ""):
    prefix = f"{prefix}: " if prefix else ""
    print(f"{prefix}{message}")


def get_pr_number_from_commit_message(commit_message: str) -> int:
    """
    コミットメッセージからPR番号を取得

    ※PR番号はコミットメッセージの1行目に含まれることを想定

    Parameters
    ----------
    commit_message : str
        コミットメッセージ

    Returns
    -------
    int
        PR番号
        ※取得できない場合には0を返す
    """
    first_row = commit_message.split("\n")[0]
    log(first_row, "first_row")

    m = PR_NUMBER_PATTERN.search(first_row)
    if not m:
        # コミットメッセージの1行目にPR番号が含まれていない場合
        return 0
    pr_number = int(m.groups()[0])
    log(pr_number, "pr_number")
    return pr_number


def get_pr_summary(pr_number: int, github_token: str, repository_name: str) -> str:
    """
    指定されたリポジトリ、PRの概要を取得

    Parameters
    ----------
    pr_number : int
        PR番号
    github_token : str
        GitHubのアクセストークン
    repository_name : str
        リポジトリ名（例: yamap55/pull_request_info_compile）

    Returns
    -------
    str
        [description]
    """
    github = Github(github_token)
    repo = github.get_repo(repository_name)
    pr = repo.get_pull(pr_number)
    log(pr.body, "pr.body")
    return pr.body


def main():
    print(f"commit_message: {COMMIT_MESSAGE}")
    print(f"repository_name: {GITHUB_REPOSITORY_NAME}")
    pr_number = get_pr_number_from_commit_message(COMMIT_MESSAGE)
    if not pr_number:
        log("PR number does not exist in the first line of the commit message")
        return
    pr_summary = get_pr_summary(pr_number, GITHUB_TOKEN, GITHUB_REPOSITORY_NAME)
    log(pr_summary, "pr_summary")


if __name__ == "__main__":
    main()
