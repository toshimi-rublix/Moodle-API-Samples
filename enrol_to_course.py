
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moodle REST API で既存ユーザー (uid) を特定コースに登録するスクリプト。
環境変数 MOODLE_TOKEN を使用します。

使い方:
  $ export MOODLE_TOKEN='YOUR_TOKEN_HERE'
  $ python enrol_user.py --uid 123
  # 必要なら:
  # $ python enrol_user.py --uid 123 --course-id 8 --role-id 5
"""

import os
import sys
import argparse
import requests
# import time  # 受講期間指定時に使用する場合にアンコメント

MOODLE_ENDPOINT = "http://localhost:8888/moodle405/webservice/rest/server.php"
MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")

def moodle_call_api(wsfunction: str, params: dict) -> dict:
    if not MOODLE_TOKEN:
        raise RuntimeError("環境変数 MOODLE_TOKEN が設定されていません。")

    payload = {
        **params,
        "wstoken": MOODLE_TOKEN,
        "wsfunction": wsfunction,
        "moodlewsrestformat": "json",
    }
    resp = requests.post(MOODLE_ENDPOINT, data=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and "exception" in data:
        msg = data.get("message", "Unknown error")
        debuginfo = data.get("debuginfo", "")
        raise RuntimeError(f"Moodle exception: {msg}\n{debuginfo}")
    return data

def flatten_one_indexed(prefix: str, record: dict) -> dict:
    """
    単一の辞書オブジェクトを Moodle REST のブラケット記法
    例: {"roleid":5,"userid":123} -> {"enrolments[0][roleid]":5, "enrolments[0][userid]":123}
    """
    return {f"{prefix}[0][{k}]": v for k, v in record.items()}

def parse_args():
    p = argparse.ArgumentParser(description="指定の uid を特定コースに登録します（manual enrol）。")
    p.add_argument("--uid", type=int, required=True, help="登録対象ユーザーのID")
    p.add_argument("--course-id", type=int, default=8, help="対象コースID（デフォルト: 8）")
    p.add_argument("--role-id", type=int, default=5, help="ロールID（標準 Student=5）")
    # 期間を付けたい場合はコメントアウトを外してください
    # p.add_argument("--days", type=int, help="受講期間（日数）。指定時に有効期間を設定")
    return p.parse_args()

def main():
    args = parse_args()

    # enrol_manual_enrol_users の前提：
    # - コースに「参加方法: Manual enrolments（手動登録）」インスタンスが有効であること
    enrolment = {
        "roleid": args.role_id,
        "userid": args.uid,
        "courseid": args.course_id,
    }

    # 期間を付けたい場合の例（--days を使う）
    # if args.days:
    #     now = int(time.time())
    #     enrolment["timestart"] = now
    #     enrolment["timeend"] = now + 86400 * args.days

    # ブラケット記法に変換
    payload = flatten_one_indexed("enrolments", enrolment)

    try:
        res = moodle_call_api("enrol_manual_enrol_users", payload)
        print("受講登録を実行しました。レスポンス:", res)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
