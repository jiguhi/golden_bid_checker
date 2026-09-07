# -*- coding: utf-8 -*-
"""Create Playwright storage_state after one manual Naver login.

Run locally:
    python local_naver_login.py
Then upload generated naver_auth_state.json in the Streamlit app once.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "naver_auth_state.json"


def logged_in(context) -> bool:
    now = time.time()
    names = {
        c.get("name")
        for c in context.cookies()
        if "naver.com" in (c.get("domain") or "").lower()
        and (c.get("expires") in (-1, None) or float(c.get("expires") or 0) > now)
    }
    return {"NID_AUT", "NID_SES"}.issubset(names)


def main():
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=False)
        except Exception:
            browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale="ko-KR", viewport={"width": 1280, "height": 900})
        page = context.new_page()
        page.goto("https://www.naver.com/", wait_until="domcontentloaded", timeout=30000)
        print("\n열린 Chrome에서 네이버에 로그인해 주세요.")
        input("로그인 완료 후 네이버 홈 화면이 보이면 여기서 Enter > ")
        page.goto("https://www.naver.com/", wait_until="domcontentloaded", timeout=30000)
        if not logged_in(context):
            browser.close()
            raise SystemExit("로그인 쿠키(NID_AUT/NID_SES)를 확인하지 못했습니다. 다시 실행해 주세요.")
        context.storage_state(path=str(OUT))
        browser.close()
    print(f"\n완료: {OUT}")
    print("이 파일을 Streamlit의 '네이버 로그인 상태 등록'에서 한 번 업로드하세요.")
    print("주의: 로그인 세션이 들어 있으므로 GitHub/메신저 등에 공유하지 마세요.")


if __name__ == "__main__":
    main()
