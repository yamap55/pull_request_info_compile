import os
import re

from github import Github

# ここも
REPOSITORY_NAME = "yamap55/pull_request_info_compile"

token = os.environ["GITHUB_TOKEN"]
commit_message = os.environ["COMMIT_MESSAGE"]
repository_name = os.environ["GITHUB_REPOSITORY_NAME"]

print(f"commit_message: {commit_message}")
print(f"repository_name: {repository_name}")

first_row = commit_message.split("\n")[0]
print(f"first_row: {first_row}")
m = re.search(r"#(\d*)", first_row)

if m:
    pr_number = m.groups()[0]
    github = Github(token)
    repo = github.get_repo(REPOSITORY_NAME)
    pr = repo.get_pull(int(pr_number))
    print(pr.body)
