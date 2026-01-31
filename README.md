# Local Video Manager (FC2-like)

ローカル環境の動画を管理・鑑賞するためのシステムです。

## 機能
- **サムネイル自動生成**: FFmpegを使用して動画からサムネイルを作成します。
- **AI自動タグ付け**: OpenAIのCLIPモデルを使用して、動画の内容からタグを自動生成します。
- **評価機能**: 10段階で動画を評価できます。
- **ランダム再生**: 保存されている動画からランダムに選んで再生できます。
- **Docker対応**: 環境を汚さずに構築可能です。

## 受け入れ要件
- `docker-compose up --build` で起動できること
- コード変更後に自動で反映されること（Backend: `--reload`, Frontend: Vite HMR）

## セットアップ

1. **動画の配置**
   デフォルトでは `/videos` フォルダをスキャンします。起動後に画面上部の **Video Directory** から任意のフォルダへ変更できます。

2. **起動**
   プロジェクトのルートディレクトリで以下のコマンドを実行します。
   ```bash
   docker-compose up --build
   ```

3. **アクセス**
   - フロントエンド: [http://localhost:5173](http://localhost:5173)
   - バックエンドAPI: [http://localhost:8000](http://localhost:8000)

4. **初期スキャン**
   画面右上の「Scan Videos」ボタンを押すと、`videos` フォルダ内の動画がスキャンされ、データベースへの登録、サムネイル作成、AIタグ付けがバックグラウンドで開始されます。

## 注意事項
- 初回のAIモデル（CLIP）のダウンロードには時間がかかる場合があります。
- 動画の数が多い場合、スキャンとタグ付けに時間がかかります。

## テスト観点（README網羅確認）
- **起動/受け入れ要件**: `docker-compose up --build` で起動し、Backendの`--reload`とVite HMRが効くことを確認する
- **動画ディレクトリ設定**: 画面上部の **Video Directory** で任意パスに変更でき、保存後にスキャン対象が切り替わる
- **初期スキャン**: 「Scan Videos」実行で新規動画がDB登録され、バックグラウンド処理が走る
- **サムネイル生成**: スキャン後にサムネイルが作成され、一覧で表示される
- **AIタグ付け**: スキャン後にタグが付与され、一覧で表示される
- **評価機能**: 0〜10の評価が保存・再表示される
- **ランダム再生**: ランダム取得が動作し、動画が存在しない場合にエラーが出る
- **アクセス**: フロントエンド`http://localhost:5173`、バックエンド`http://localhost:8000`にアクセスできる

## CI（自動テスト）
GitHub Actionsでバックエンドのテストを自動実行します。

1. このリポジトリをGitHubへpush
2. GitHubの「Actions」でCIが有効化されていることを確認
3. `push` / `pull_request` 時に以下が自動実行されます:
   - **ユニットテスト**: `pytest backend/tests`（モック使用）
   - **統合テスト**: Dockerでバックエンドを起動し、実際のFFmpeg処理を含むAPIテスト

### 統合テストのローカル実行（Linux / macOS）
```bash
# テスト用動画作成
./scripts/create_test_video.sh

# バックエンド起動
docker compose -f docker-compose.integration.yml up -d --build

# API起動待ち後にテスト実行
pip install httpx pytest
API_BASE=http://localhost:8000 pytest backend/tests -m integration -v

# 停止
docker compose -f docker-compose.integration.yml down
```
