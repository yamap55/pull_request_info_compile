import os
import re
from typing import Any

from github import Github


def log(message: Any, prefix: Any = ""):
    prefix = f"{prefix}: " if prefix else ""
    print(f"{prefix}{message}")


def get_pr_number_from_commit_message(commit_message: str, pattern: re.Pattern) -> int:
    """
    コミットメッセージからPR番号を取得

    ※PR番号はコミットメッセージの1行目に含まれることを想定

    Parameters
    ----------
    commit_message : str
        コミットメッセージ
    pattern: re.Pattern
        PR番号を表現する正規表現
        グループマッチの1つ目を使用する

    Returns
    -------
    int
        PR番号
        ※取得できない場合には0を返す
    """
    first_row = commit_message.split("\n")[0]
    log(first_row, "first_row")

    m = pattern.search(first_row)
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
        PRの概要
    """
    github = Github(github_token)
    repo = github.get_repo(repository_name)
    body = repo.get_pull(pr_number).body
    log(body, "pr.body")
    return body


def extract_target_section(summary: str, target_section_title_row: str) -> str:
    """
    対象のセクションのみを抽出

    Parameters
    ----------
    summary : str
        抽出対象のサマリ
    target_section_title_row : str
        抽出対象であるセクションのタイトル行（完全一致）

    Returns
    -------
    str
        抽出されたセクション
    """
    log(summary, "summary")
    messages = summary.split("\n")
    if target_section_title_row not in messages:
        # 対象行がない場合は空文字を返す
        # 本来であれば例外を投げた方が良いが、運用上mainブランチにマージ時に実行される事を想定しているため、ここで例外を投げても補足される可能性は低い
        return ""

    # 対象のセクションより前のメッセージを除去
    i = messages.index(target_section_title_row)
    log(i, "i")
    remove_before_messages = messages[i:]
    log(remove_before_messages, "remove_before_messages")

    # 対象のセクションより後のメッセージを除去
    # NOTE: 対象の文字列がh2であることに依存しているので汎用的にするのであれば修正の必要あり
    search_index_generator = (
        i for i, message in enumerate(remove_before_messages) if re.search("^#{1,2} ", message)
    )
    next(search_index_generator)  # 最初にマッチするのは対象の文字列なのでスキップ
    i = next(search_index_generator, -1)
    log(i, "i")
    target_messages = remove_before_messages if i == -1 else remove_before_messages[:i]
    log(target_messages, "target_messages")

    return "\n".join(target_messages)


def main():
    GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
    COMMIT_MESSAGE = os.environ["COMMIT_MESSAGE"]
    GITHUB_REPOSITORY_NAME = os.environ["GITHUB_REPOSITORY_NAME"]
    PR_NUMBER_PATTERN = re.compile(r"#(\d*)")
    TARGET_SECTION_TITLE_ROW = "## 結合テスト観点"

    log(f"commit_message: {COMMIT_MESSAGE}")
    log(f"repository_name: {GITHUB_REPOSITORY_NAME}")
    pr_number = get_pr_number_from_commit_message(COMMIT_MESSAGE, PR_NUMBER_PATTERN)
    if not pr_number:
        log("PR number does not exist in the first line of the commit message")
        return
    pr_summary = get_pr_summary(pr_number, GITHUB_TOKEN, GITHUB_REPOSITORY_NAME)
    log(pr_summary, "pr_summary")
    integration_test_point = extract_target_section(pr_summary, TARGET_SECTION_TITLE_ROW)
    log(integration_test_point, "integration_test_point")


if __name__ == "__main__":
    main()
