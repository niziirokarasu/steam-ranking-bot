import logging
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

# Discordの1メッセージ上限2000文字に対してマージンを取る
_MAX_CHARS = 1900


def build_message(
    current_items: list[dict],
    diff: dict | None,
    region: str,
    top_n: int,
    is_first: bool,
) -> str:
    """Discord投稿用のメッセージ本文を組み立てる。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = []

    lines += [
        "📊 **Steam売れ筋ランキング定期チェック**",
        f"取得日時：{now}",
        f"対象地域：{region}",
        f"対象：Steam売れ筋 Top {top_n}",
        "",
        "🏆 **現在の上位10件**",
    ]
    for item in current_items[:10]:
        lines.append(f"{item['rank']}. {item['title']}")

    if is_first or diff is None:
        lines += [
            "",
            "※ 初回取得のため差分比較はありません。",
        ]
    else:
        if diff["new_entries"]:
            lines += ["", "🆕 **新規ランクイン**"]
            for item in diff["new_entries"]:
                lines.append(f"{item['rank']}位：{item['title']}")

        significant_up = [x for x in diff["rank_up"] if x["diff"] >= 10]
        if significant_up:
            lines += ["", "⬆️ **大きく上昇**"]
            for item in significant_up:
                lines.append(
                    f"{item['rank']}位：{item['title']}"
                    f"（前回{item['prev_rank']}位 → 今回{item['rank']}位 / +{item['diff']}）"
                )

        significant_down = [x for x in diff["rank_down"] if abs(x["diff"]) >= 10]
        if significant_down:
            lines += ["", "⬇️ **大きく下降**"]
            for item in significant_down:
                lines.append(
                    f"{item['rank']}位：{item['title']}"
                    f"（前回{item['prev_rank']}位 → 今回{item['rank']}位 / {item['diff']}）"
                )

        if diff["dropped"]:
            lines += ["", "📉 **圏外落ち**"]
            for item in diff["dropped"]:
                lines.append(f"{item['title']}（前回{item['rank']}位）")

    lines += [
        "",
        "─────────────────────────",
        "補足：Steam売れ筋ランキングは販売本数ではなく、"
        "DLC・ゲーム内課金なども含む**売上金額ベース**のランキングです。",
    ]

    return "\n".join(lines)


def send_discord_message(content: str, webhook_url: str):
    """Discord Webhookにメッセージを送信する。長い場合は分割して送る。"""
    if not webhook_url:
        logger.error("DISCORD_WEBHOOK_URLが設定されていません。")
        raise ValueError("DISCORD_WEBHOOK_URLが未設定です。.envを確認してください。")

    for chunk in _split_message(content):
        _post(chunk, webhook_url)


def _post(content: str, webhook_url: str):
    try:
        response = requests.post(
            webhook_url,
            json={"content": content},
            timeout=10,
        )
        response.raise_for_status()
        logger.info("Discord通知送信完了")
    except requests.exceptions.HTTPError as e:
        logger.error(f"Discord通知失敗 (HTTPエラー): {e} / レスポンス: {e.response.text}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Discord通知失敗: {e}")
        raise


def _split_message(content: str) -> list[str]:
    """メッセージが長すぎる場合、行単位で分割する。"""
    if len(content) <= _MAX_CHARS:
        return [content]

    chunks: list[str] = []
    current = ""
    for line in content.split("\n"):
        candidate = current + line + "\n"
        if len(candidate) > _MAX_CHARS:
            if current:
                chunks.append(current.rstrip())
            current = line + "\n"
        else:
            current = candidate

    if current:
        chunks.append(current.rstrip())

    return chunks
