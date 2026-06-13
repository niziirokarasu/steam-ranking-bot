"""
Steam売れ筋ランキング Discord通知Bot

使い方:
  python main.py run                # 1回取得して通知判定
  python main.py run --force-notify # 変動がなくても強制通知
"""

import argparse
import logging
import os
import sys

import config
from storage import load_previous_ranking, save_current_ranking
from diff_checker import compare_rankings, has_significant_changes
from discord_notifier import build_message, send_discord_message
from steam_scraper import fetch_top_sellers


def setup_logging():
    os.makedirs(config.LOG_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(config.LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def cmd_run(force_notify: bool = False):
    logger = logging.getLogger(__name__)
    logger.info("=== ランキング取得開始 ===")

    # Step 1: Steam売れ筋ランキングを取得
    try:
        items = fetch_top_sellers(region=config.STEAM_REGION, top_n=config.TOP_N)
    except Exception as e:
        logger.error(f"ランキング取得に失敗しました: {e}")
        return

    if not items:
        logger.error("取得件数が0件でした。処理を中断します。")
        return

    # Step 2: 前回データを読み込んで差分チェック
    previous = load_previous_ranking()
    is_first = previous is None

    if is_first:
        logger.info("初回実行のため差分比較をスキップします。")
        diff = None
        should_notify = True
    else:
        diff = compare_rankings(previous, items)
        should_notify = has_significant_changes(diff) or force_notify
        logger.info(
            f"差分: 新規={len(diff['new_entries'])}, "
            f"上昇={len(diff['rank_up'])}, "
            f"下降={len(diff['rank_down'])}, "
            f"圏外={len(diff['dropped'])}"
        )

    if force_notify and not should_notify:
        logger.info("--force-notify が指定されたため強制通知します。")
        should_notify = True

    # Step 3: Discord通知
    if should_notify:
        try:
            message = build_message(
                current_items=items,
                diff=diff,
                region=config.STEAM_REGION,
                top_n=config.TOP_N,
                is_first=is_first,
            )
            send_discord_message(message, config.DISCORD_WEBHOOK_URL)
        except Exception as e:
            logger.error(f"Discord通知に失敗しました: {e}")
    else:
        logger.info("通知条件を満たしていないためDiscord通知をスキップしました。")

    # Step 4: 今回のランキングをJSONに保存（次回の「前回データ」になる）
    try:
        save_current_ranking(items)
    except Exception as e:
        logger.error(f"ランキングの保存に失敗しました: {e}")
        return

    logger.info("=== ランキング取得完了 ===")


def main():
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Steam売れ筋ランキング Discord通知Bot"
    )
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="1回だけ取得して通知判定する")
    run_parser.add_argument(
        "--force-notify",
        action="store_true",
        help="変動の有無に関わらず強制的にDiscordへ通知する",
    )

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(force_notify=args.force_notify)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
