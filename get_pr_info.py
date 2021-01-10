import os
import re
from typing import Any

import requests
from atlassian import Jira
from github import Github
from requests.auth import HTTPBasicAuth


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
    m = pattern.search(first_row)
    if not m:
        # コミットメッセージの1行目にPR番号が含まれていない場合
        return 0
    pr_number = int(m.groups()[0])
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
    messages = summary.splitlines()
    if target_section_title_row not in messages:
        # 対象行がない場合は空文字を返す
        # 本来であれば例外を投げた方が良いが、運用上mainブランチにマージ時に実行される事を想定しているため、ここで例外を投げても補足される可能性は低い
        return ""

    # 対象のセクションより前のメッセージを除去
    i = messages.index(target_section_title_row)
    remove_before_messages = messages[i:]

    # 対象のセクションより後のメッセージを除去
    # NOTE: 対象の文字列がh2であることに依存しているので汎用的にするのであれば修正の必要あり
    search_index_generator = (
        i for i, message in enumerate(remove_before_messages) if re.search("^#{1,2} ", message)
    )
    next(search_index_generator)  # 最初にマッチするのは対象の文字列なのでスキップ
    i = next(search_index_generator, -1)
    target_messages = remove_before_messages if i == -1 else remove_before_messages[:i]

    return "\n".join(target_messages)


def create_atlassian_session_with_auth(email: str, token: str) -> requests.Session:
    """
    認証付きのリクエストセッションを作成

    Parameters
    ----------
    email : str
        atlassianに登録しているEメールアドレス
    token : str
        atlassianの認証トークン

    Returns
    -------
    requests.Session
        リクエストセッション
    """
    session = requests.Session()
    session.auth = HTTPBasicAuth(email, token)
    return session


def add_comment_to_jira_issue(jira_client: Jira, project: str, summary: str, comment: str) -> None:
    """
    指定された条件で取得されるIssueにコメントを追加

    Parameters
    ----------
    jira_client : Jira
        Jiraクライアント
    project : str
        プロジェクト名（キーとは異なるので注意）
    summary : str
        コメントを追加するIssueのsummary（曖昧検索）
    comment : str
        [description]
    """
    # TODO: 完全一致での指定がわからず、IssueのSummaryは曖昧検索で行っている
    JQL = f'project = "{project}" AND summary ~ "{summary}" AND status!=Done  order by created DESC'
    data = jira_client.jql(JQL)
    issue_id = data["issues"][0]["key"]  # type: ignore
    jira_client.issue_add_comment(issue_key=issue_id, comment=comment)


def main():
    GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
    COMMIT_MESSAGE = os.environ["COMMIT_MESSAGE"]
    GITHUB_REPOSITORY_NAME = os.environ["GITHUB_REPOSITORY_NAME"]
    PR_NUMBER_PATTERN = re.compile(r"#(\d*)")
    TARGET_SECTION_TITLE_ROW = "## 結合テスト観点"

    ATLASSIAN_API_TOKEN = os.environ["ATLASSIAN_API_TOKEN"]
    ATLASSIAN_EMAIL = os.environ["ATLASSIAN_EMAIL"]
    ATLASSIAN_URL = os.environ["ATLASSIAN_URL"]
    JIRA_TARGET_PROJECT = os.environ["JIRA_TARGET_PROJECT"]
    JIRA_TARGET_ISSUE_SUMMARY = os.environ["JIRA_TARGET_ISSUE_SUMMARY"]

    log(f"commit_message: {COMMIT_MESSAGE}")
    log(f"repository_name: {GITHUB_REPOSITORY_NAME}")
    pr_number = get_pr_number_from_commit_message(COMMIT_MESSAGE, PR_NUMBER_PATTERN)
    log(pr_number, "pr_number")
    if not pr_number:
        # TODO: 例外を投げて通知
        log("PR number does not exist in the first line of the commit message")
        return
    pr_summary = get_pr_summary(pr_number, GITHUB_TOKEN, GITHUB_REPOSITORY_NAME)
    log(pr_summary, "pr_summary")
    integration_test_point = extract_target_section(pr_summary, TARGET_SECTION_TITLE_ROW)
    if not integration_test_point:
        # TODO: 例外を投げて通知
        log("target section title dose not exists.")
        return
    log(integration_test_point, "integration_test_point")

    try:
        session = create_atlassian_session_with_auth(ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN)
        jira = Jira(url=ATLASSIAN_URL, session=session)
        add_comment_to_jira_issue(
            jira, JIRA_TARGET_PROJECT, JIRA_TARGET_ISSUE_SUMMARY, integration_test_point
        )
    except Exception as e:
        # TODO: 例外時に公開リポジトリのログに出力されて欲しくないものが出力されるかもしれないため例外をもみ消す
        print(e)


if __name__ == "__main__":
    main()
