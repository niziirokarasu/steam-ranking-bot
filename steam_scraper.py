"""
Steam売れ筋ランキング取得モジュール。

取得先: https://store.steampowered.com/search/results/?filter=topsellers&json=1
レスポンスは {"items": [{"name": ..., "logo": ...}, ...]} の形式。
logo URLに app_id が含まれるため、そこから抽出する。

Steam側のAPI仕様変更が起きた場合は fetch_top_sellers() を修正してください。
"""

import re
import time
import logging
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

SEARCH_URL = "https://store.steampowered.com/search/results/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}


def _app_id_from_logo(logo_url: str) -> str | None:
    m = re.search(r"/apps/(\d+)/", logo_url)
    return m.group(1) if m else None


def fetch_top_sellers(region: str = "JP", top_n: int = 50) -> list[dict]:
    """
    Steamの売れ筋ランキングを取得して返す。

    Returns:
        各要素が以下のキーを持つ list[dict]:
        rank, title, url, app_id, price, is_free, timestamp
    """
    logger.info(f"Steam売れ筋ランキング取得開始: 地域={region}, 上位{top_n}件")

    params = {
        "filter": "topsellers",
        "cc": region,
        "l": "japanese",
        "start": 0,
        "count": top_n,
        "json": 1,
    }

    # Steam側への負荷軽減のため1秒待機
    time.sleep(1)

    try:
        response = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.ConnectionError as e:
        logger.error(f"ネット接続エラー: {e}")
        raise
    except requests.exceptions.Timeout:
        logger.error("Steamへのリクエストがタイムアウトしました。")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"Steamページ取得失敗 (HTTPエラー): {e}")
        raise
    except ValueError as e:
        logger.error(f"SteamのレスポンスがJSON形式ではありません: {e}")
        raise

    # --- レスポンス解析 ---
    # 現在の形式: {"desc": "", "items": [{"name": "...", "logo": "..."}, ...]}
    raw_items = data.get("items", [])

    if not raw_items:
        # フォールバック: 旧形式の results_html も試みる
        results_html = data.get("results_html", "")
        if results_html:
            logger.warning("旧形式(results_html)を検出。_parse_html_fallback() を使用します。")
            return _parse_html_fallback(results_html, top_n)

        logger.error(
            "items も results_html も空です。"
            "Steam APIの仕様変更の可能性があります。"
            "steam_scraper.py の fetch_top_sellers() を確認してください。"
        )
        raise ValueError("Steam APIから結果を取得できませんでした。")

    timestamp = datetime.now().isoformat()
    items = []

    for rank, raw in enumerate(raw_items[:top_n], start=1):
        title = raw.get("name", "").strip()
        if not title:
            logger.warning(f"rank={rank}: タイトルが空のためスキップします。")
            continue

        logo_url = raw.get("logo", "")
        app_id = _app_id_from_logo(logo_url)
        url = f"https://store.steampowered.com/app/{app_id}/" if app_id else ""

        items.append({
            "rank": rank,
            "title": title,
            "url": url,
            "app_id": app_id,
            "price": "",     # 現在のAPIでは価格情報なし
            "is_free": False,
            "timestamp": timestamp,
        })

    logger.info(f"取得完了: {len(items)}件")
    return items


def _parse_html_fallback(results_html: str, top_n: int) -> list[dict]:
    """
    旧形式（results_html）への後方互換パーサー。
    Steam APIが旧形式に戻った場合に自動で使われる。
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(results_html, "html.parser")
    rows = soup.select("a.search_result_row")

    if not rows:
        raise ValueError("HTMLからランキング行を取得できませんでした。")

    timestamp = datetime.now().isoformat()
    items = []

    for rank, row in enumerate(rows, start=1):
        if rank > top_n:
            break
        title_elem = row.select_one(".title")
        title = title_elem.get_text(strip=True) if title_elem else ""
        if not title:
            continue

        url = row.get("href", "").split("?")[0]
        app_id = row.get("data-ds-appid", "").split(",")[0] or None
        if not app_id:
            m = re.search(r"/app/(\d+)/", url)
            app_id = m.group(1) if m else None

        price_elem = row.select_one(".search_price") or row.select_one(".discount_final_price")
        price_text = price_elem.get_text(strip=True) if price_elem else ""
        is_free = any(kw in price_text for kw in ["無料", "Free", "free"])

        items.append({
            "rank": rank,
            "title": title,
            "url": url,
            "app_id": app_id,
            "price": price_text,
            "is_free": is_free,
            "timestamp": timestamp,
        })

    return items
