import os

environment_variables = [
    "GITHUB_EVENT_NAME",
    "GITHUB_EVENT_PATH",
    "GITHUB_WORKSPACE",
    "GITHUB_SHA",
    "GITHUB_REF",
    "GITHUB_HEAD_REF",
    "GITHUB_BASE_REF",
    "GITHUB_SERVER_URL",
    "GITHUB_API_URL",
    "GITHUB_GRAPHQL_URL",
]
for var in environment_variables:
    print(f"{var} : {os.environ.get(var)}")
