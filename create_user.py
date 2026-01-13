
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moodle REST API でユーザーを作成するスクリプト。
環境変数 MOODLE_TOKEN を使用します。

使い方:
  $ export MOODLE_TOKEN='YOUR_TOKEN_HERE'
  $ python create_user.py
"""

import os
import sys
import requests

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

def flatten_params(prefix: str, data: dict) -> dict:
    """ネストした dict を Moodle REST 用ブラケット記法に変換"""
    flat = {}
    for key, value in data.items():
        flat[f"{prefix}[0][{key}]"] = value
    return flat

def main():
    # 作成したいユーザー情報（必要に応じて変更）
    new_user = {
        "username":  "testuser001", # ← 大文字を含むとエラーになる
        "password":  "P@ssw0rd!",  # サイトのパスワードポリシーに合わせる
        "firstname": "テストユーザ",
        "lastname":  "001",
        "email":     "testuser001@example.com",
        "auth":      "manual",
        "lang":      "ja",
        "country":   "JP",
    }

    try:
        # 既存ユーザー検索（emailで重複回避）
        found = moodle_call_api("core_user_get_users", {
            "criteria[0][key]": "email",
            "criteria[0][value]": new_user["email"],
        })

        users = found.get("users", [])
        if users:
            print(f"既存ユーザーが見つかりました。ID={users[0]['id']}")
            sys.exit(0)

        # 見つからなければ作成（new_userをブラケット記法に変換）
        created = moodle_call_api("core_user_create_users", flatten_params("users", new_user))

        if not created or "id" not in created[0]:
            raise RuntimeError("ユーザー作成の返り値にIDが含まれていません。")

        print(f"ユーザーを作成しました。ID={created[0]['id']}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()