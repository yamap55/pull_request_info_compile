# pull_request_info_compile

GitHub Actions で以下を実現するための試行錯誤するリポジトリ

- 規定のブランチへの push 時に起動
- PR からのマージの場合、PR の概要を取得

## 環境構築

### 事前準備

- Docker インストール
- VSCode インストール
- VSCode の拡張機能「Remote - Containers」インストール
  - https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers
- 本リポジトリの clone
- `.env` ファイルを空ファイルでプロジェクト直下に作成

### 開発手順

1. VSCode 起動
2. 左下の緑色のアイコンクリック
3. 「Remote-Containersa: Reopen in Container」クリック
4. しばらく待つ
   - 初回の場合コンテナ image の取得や作成が行われる
5. 起動したら開発可能

### 環境変数

ローカルで実行させたい場合には以下の環境変数の設定が必要
GitHub Actions で動作させる場合はコンテキストから取得して設定ファイル内で環境変数に設定する

```
GITHUB_TOKEN=xxxxxxxxxxxx
COMMIT_MESSAGE=[refactor] script (#8)\nhoge\nhugahuga
GITHUB_REPOSITORY_NAME=yamap55/pull_request_info_compile

ATLASSIAN_EMAIL=example@example.com
ATLASSIAN_API_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxx
ATLASSIAN_URL=https://xxxxxxx.atlassian.net/
JIRA_TARGET_PROJECT=EXAMPLE-PROJECT
JIRA_TARGET_ISSUE_SUMMARY=結合テスト観点
```
