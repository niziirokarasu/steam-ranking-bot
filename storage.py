"""
ランキングデータのJSON保存・読み込み。

保存先: data/latest_ranking.json
GitHub Actionsで実行した後、このファイルをコミットすることで
次回実行時の「前回データ」として使う。
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).parent
_DATA_DIR = _BASE_DIR / "data"
_RANKING_FILE = _DATA_DIR / "latest_ranking.json"


def load_previous_ranking() -> list[dict] | None:
    """前回保存したランキングを返す。ファイルがなければ None（初回扱い）。"""
    if not _RANKING_FILE.exists():
        logger.info("前回データなし（初回実行）")
        return None
    try:
        with open(_RANKING_FILE, encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"前回ランキング読み込み: {len(data)}件")
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"前回ランキングの読み込み失敗: {e}")
        return None


def save_current_ranking(items: list[dict]):
    """今回のランキングを JSON ファイルに保存する。"""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(_RANKING_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        logger.info(f"ランキング保存完了: {_RANKING_FILE}")
    except OSError as e:
        logger.error(f"ランキング保存失敗: {e}")
        raise
