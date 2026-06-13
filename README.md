# Steam売れ筋ランキング Discord通知Bot

Steamの売れ筋ランキング Top 50を1時間ごとに取得し、  
前回との差分をDiscordへ通知するBotです。  
**GitHub Actionsで無料で定期実行できます。**

> Steam売れ筋ランキングは販売本数ではなく、DLC・ゲーム内課金も含む**売上金額ベース**のランキングです。

---

## このツールでできること

- Steam公式の売れ筋ランキング上位50件を1時間ごとに自動取得（GitHub Actions）
- 前回取得時との差分を自動検出
  - 🆕 新規ランクイン
  - ⬆️ 大きく上昇したゲーム（+10以上）
  - ⬇️ 大きく下降したゲーム（-10以上）
  - 📉 圏外落ち
- 重要な変動があるときだけDiscordに通知
- 取得結果を `data/latest_ranking.json` に保存（GitHubリポジトリに蓄積）

---

## 必要なもの

- GitHubアカウント（無料）
- Discordサーバーの管理権限（Webhook URLの発行に必要）
- ローカルテスト用：Python 3.12以上

---

## セットアップ手順

### 1. GitHubリポジトリを作る

1. GitHub（https://github.com）にログイン
2. 右上の「+」→「New repository」をクリック
3. リポジトリ名を入力（例：`steam-ranking-bot`）
4. **Private** を選択（Webhook URLを含むファイルをPublicにしないため）
5. 「Create repository」をクリック

---

### 2. このフォルダをGitHubにプッシュする

コマンドプロンプトまたはターミナルで `steam_ranking_discord_bot` フォルダの中に入り、以下を実行します。

```bash
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/あなたのユーザー名/steam-ranking-bot.git
git push -u origin main
```

> GitHubのリポジトリページに表示されているコマンドをそのままコピーしても構いません。

---

### 3. Discord Webhook URLを取得する

1. Discordを開き、通知を送りたいチャンネルを右クリック →「チャンネルを編集」
2. 左メニューの「**連携サービス**」→「**ウェブフックを作成**」
3. 名前を入力して「**ウェブフックのURLをコピー**」
4. URLをメモしておく（`https://discord.com/api/webhooks/...` の形式）

---

### 4. GitHub Secrets に Webhook URL を登録する

GitHubリポジトリの画面で：

1. 「**Settings**」タブ → 左メニューの「**Secrets and variables**」→「**Actions**」
2. 「**New repository secret**」をクリック
3. 以下を入力して「Add secret」：
   - Name：`DISCORD_WEBHOOK_URL`
   - Secret：手順3でコピーしたURL

---

### 5. GitHub Actions を有効にする

1. GitHubリポジトリの「**Actions**」タブをクリック
2. 「I understand my workflows, go ahead and enable them」をクリック

これで毎時0分（UTC）に自動実行されます。

---

### 6. 手動でテスト実行する

GitHubリポジトリの「**Actions**」タブ →「**Steam売れ筋ランキング チェック**」→「**Run workflow**」ボタンをクリックします。

数分後にDiscordへ通知が届けば成功です。

---

## ローカルでテスト実行する方法

本番はGitHub Actionsですが、ローカルでも動作確認できます。

### ライブラリのインストール

```bash
cd steam_ranking_discord_bot
pip install -r requirements.txt
```

### .envファイルを作る

```bash
copy .env.example .env   # Windowsの場合
```

`.env` をメモ帳で開き、Webhook URLを設定します：

```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxxx/yyyyy
STEAM_REGION=JP
TOP_N=50
```

### 実行

```bash
# 1回実行（差分があるときだけ通知）
python main.py run

# 強制通知（テスト用）
python main.py run --force-notify
```

初回実行後に `data/latest_ranking.json` が作成されます。  
2回目以降は前回との差分が検出されます。

---

## ファイル構成

```
steam_ranking_discord_bot/
├── .github/
│   └── workflows/
│       └── steam-ranking.yml   ← GitHub Actions の定義
├── data/
│   └── latest_ranking.json     ← 前回ランキング（自動更新）
├── main.py                     ← CLIの入口
├── config.py                   ← 設定値の読み込み
├── steam_scraper.py            ← Steam取得（HTML解析部）
├── storage.py                  ← JSONファイルの読み書き
├── diff_checker.py             ← 差分検出
├── discord_notifier.py         ← Discord Webhook通知
├── requirements.txt
├── .env.example
├── .env                        ← ローカルのみ（gitignore済み）
├── .gitignore
└── README.md
```

---

## 注意事項

### GitHub Actionsの制限
- **無料枠**：プライベートリポジトリは月2,000分まで無料。1回約1〜2分 × 24時間 × 30日 ≒ 720〜1,440分なので通常は無料範囲内です。パブリックリポジトリは無制限。
- **スケジュール遅延**：GitHubの混雑状況によっては設定時刻より最大1時間遅れることがあります。
- **60日間未使用で停止**：リポジトリに60日間コミットがないとスケジュール実行が停止されます。手動で再有効化するか、`data/latest_ranking.json` の更新コミットが毎回入るため通常は問題ありません。

### Steamページ構造変更への対応
- `steam_scraper.py` の `_parse_rows()` 関数に解析処理を集約しています
- ランキングが取得できなくなった場合はここを修正してください
- `logs/app.log` にエラーの詳細が記録されます

### Discord通知条件
- 初回：上位10件を必ず通知
- 2回目以降：新規ランクイン・10位以上の変動・圏外落ちがある場合のみ通知
- `--force-notify` オプションで強制通知（テスト時など）

---

## トラブルシューティング

| 症状 | 対処法 |
|------|--------|
| GitHub ActionsでDiscord通知が来ない | Secretsの `DISCORD_WEBHOOK_URL` が正しく設定されているか確認 |
| `Run workflow` を押してもエラー | Actionsタブでログを確認。Steamへの接続失敗の可能性あり |
| ランキングが0件で取得される | SteamのHTML構造が変わった可能性。`steam_scraper.py` の `_parse_rows()` を確認 |
| ローカルで「URLが未設定」エラー | `.env` ファイルを作成し、`DISCORD_WEBHOOK_URL=` を設定してください |
| コミットが失敗する | リポジトリの Settings → Actions → General → 「Workflow permissions」を「Read and write permissions」に変更 |
