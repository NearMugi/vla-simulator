---
name: python-env-policy
description: Pythonコードの作成、実行、デバッグ、またはパッケージのインストールを行う際に使用します。
---
# Goal
システムのグローバル環境を汚染せず、必ずasdfとPoetryを使用した仮想環境内でスクリプトを実行・管理する。

# Instructions
- Pythonスクリプトを使用したい場合はasdfとPoetryを使用して仮想環境を作成すること。
- Pythonスクリプトを実行する際は、必ず `poetry run python <ファイル名>` を使用すること。
- 新しいパッケージを追加する際は `pip` ではなく、必ず `poetry add <パッケージ名>` を使用すること。
- 環境が有効か不明な場合は、実行前に `poetry env info` で確認すること。