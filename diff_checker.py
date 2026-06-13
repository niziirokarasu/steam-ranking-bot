import logging

logger = logging.getLogger(__name__)


def _build_index(items: list[dict]) -> dict[str, dict]:
    """app_idがあればそれをキー、なければタイトルをキーにして辞書を作る。"""
    index = {}
    for item in items:
        key = item.get("app_id") or item["title"]
        index[key] = item
    return index


def compare_rankings(previous: list[dict], current: list[dict]) -> dict:
    """
    前回と今回のランキングを比較して差分を返す。

    Returns:
        {
            "new_entries": [...],   # 新規ランクイン
            "rank_up":    [...],   # 順位上昇（diffキー付き）
            "rank_down":  [...],   # 順位下降（diffキー付き）
            "dropped":    [...],   # 圏外落ち
            "unchanged":  [...],   # 変動なし
        }

    diff の計算式: prev_rank - curr_rank
        正 → 上昇（小さい数字 = 上位なので、数字が減ったら上昇）
        負 → 下降
    """
    prev_index = _build_index(previous)
    curr_index = _build_index(current)

    prev_keys = set(prev_index.keys())
    curr_keys = set(curr_index.keys())

    new_entries: list[dict] = []
    rank_up:    list[dict] = []
    rank_down:  list[dict] = []
    dropped:    list[dict] = []
    unchanged:  list[dict] = []

    for key in curr_keys - prev_keys:
        new_entries.append(curr_index[key])

    for key in curr_keys & prev_keys:
        curr_item  = curr_index[key]
        prev_item  = prev_index[key]
        prev_rank  = prev_item["rank"]
        curr_rank  = curr_item["rank"]
        diff       = prev_rank - curr_rank  # 正=上昇, 負=下降

        enriched = {**curr_item, "prev_rank": prev_rank, "diff": diff}
        if diff > 0:
            rank_up.append(enriched)
        elif diff < 0:
            rank_down.append(enriched)
        else:
            unchanged.append(curr_item)

    for key in prev_keys - curr_keys:
        dropped.append(prev_index[key])

    new_entries.sort(key=lambda x: x["rank"])
    rank_up.sort(key=lambda x: x["diff"], reverse=True)
    rank_down.sort(key=lambda x: x["diff"])
    dropped.sort(key=lambda x: x["rank"])

    return {
        "new_entries": new_entries,
        "rank_up":    rank_up,
        "rank_down":  rank_down,
        "dropped":    dropped,
        "unchanged":  unchanged,
    }


def has_significant_changes(diff: dict, threshold: int = 10) -> bool:
    """通知すべき重要な変動があるかを判定する。"""
    if diff["new_entries"]:
        return True
    if any(item["diff"] >= threshold for item in diff["rank_up"]):
        return True
    if any(abs(item["diff"]) >= threshold for item in diff["rank_down"]):
        return True
    if diff["dropped"]:
        return True
    return False
