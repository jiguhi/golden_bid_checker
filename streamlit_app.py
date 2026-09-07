# -*- coding: utf-8 -*-
"""황금이네 순위체커 - GitHub/Streamlit 배포 버전.

인증 흐름
1) local_naver_login.py를 로컬 PC에서 1회 실행하여 naver_auth_state.json 생성
2) 이 앱의 사이드바에서 파일을 1회 업로드
3) Supabase가 설정되어 있으면 인증 상태를 영구 저장
4) 이후 조회 시 서버가 저장된 Playwright storage_state를 자동 재사용
"""
from __future__ import annotations

import io
import json
import os
import sys
import asyncio
import time
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except AttributeError:
        pass

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
AUTH_FILE = BASE_DIR / ".auth" / "naver_auth_state.json"
RESULT_DIR = BASE_DIR / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="황금이네 순위체커", page_icon="🔎", layout="wide")


def _secret(section: str, key: str, default: str = "") -> str:
    try:
        if section in st.secrets and key in st.secrets[section]:
            return str(st.secrets[section][key])
    except Exception:
        pass
    return default


# SearchAd API 실제 키는 GitHub 파일 대신 Streamlit Secrets에서 주입합니다.
os.environ.setdefault("NAVER_SEARCHAD_CUSTOMER_ID", _secret("naver_searchad", "customer_id"))
os.environ.setdefault("NAVER_SEARCHAD_API_KEY", _secret("naver_searchad", "api_key"))
os.environ.setdefault("NAVER_SEARCHAD_SECRET_KEY", _secret("naver_searchad", "secret_key"))
os.environ["GOLDEN_BROWSER_MODE"] = "state"
os.environ["GOLDEN_AUTH_STATE_FILE"] = str(AUTH_FILE)
os.environ.setdefault("GOLDEN_DEBUG_CAPTURE_ALL", "0")

import golden_integrated_checker as core
from auth_store import AuthStore

core.BROWSER_MODE = "state"
core.AUTH_STATE_FILE = AUTH_FILE


def auth_store() -> AuthStore:
    return AuthStore(
        local_path=AUTH_FILE,
        supabase_url=_secret("supabase", "url"),
        supabase_key=_secret("supabase", "service_key"),
        table=_secret("supabase", "table", "naver_sessions"),
        session_key=_secret("supabase", "session_key", "golden-default"),
    )


STORE = auth_store()


class LiveLog(io.StringIO):
    def __init__(self, placeholder):
        super().__init__()
        self.placeholder = placeholder

    def write(self, text):
        n = super().write(text)
        self.placeholder.code(self.getvalue()[-12000:] or "실행 중...", language=None)
        return n


def validate_state_structure(state: dict) -> tuple[bool, str]:
    if not isinstance(state, dict) or not isinstance(state.get("cookies"), list):
        return False, "Playwright storage_state 형식이 아닙니다."
    now = time.time()
    names = set()
    for c in state["cookies"]:
        if "naver.com" not in str(c.get("domain", "")).lower():
            continue
        exp = c.get("expires", -1)
        if exp not in (-1, None):
            try:
                if float(exp) <= now:
                    continue
            except Exception:
                pass
        names.add(c.get("name"))
    missing = {"NID_AUT", "NID_SES"} - names
    if missing:
        return False, f"네이버 로그인 쿠키가 부족합니다: {', '.join(sorted(missing))}"
    return True, "로그인 쿠키 확인"


def materialize_auth() -> Path:
    path = STORE.materialize()
    if not path:
        raise core.StopRun("저장된 네이버 로그인 상태가 없습니다. 먼저 로그인 상태 파일을 등록하세요.")
    core.AUTH_STATE_FILE = path
    return path


def check_saved_session() -> tuple[bool, str]:
    materialize_auth()
    from playwright.sync_api import sync_playwright
    browser = None
    try:
        with sync_playwright() as p:
            browser, context = core._launch_saved_state_browser(p)
            page = context.new_page()
            page.goto("https://www.naver.com/", wait_until="domcontentloaded", timeout=30000)
            root = core.Document(core.read_page_html(page)).root
            core.security_check(root)
            if not core.logged_in(context):
                return False, "저장된 네이버 세션이 만료되었거나 로그아웃되었습니다."
            return True, "저장된 네이버 로그인 세션이 정상입니다."
    except Exception as e:
        return False, str(e)
    finally:
        try:
            if browser is not None:
                browser.close()
        except Exception:
            pass


def result_dataframe(results):
    rows = []
    for row in results:
        item = {"키워드": row["keyword"]}
        for surface in core.SURFACES:
            result = row.get("surfaces", {}).get(surface)
            item[surface] = core.display(result) if result else "미조회"
        rows.append(item)
    return pd.DataFrame(rows)


def plan_dataframe(plan):
    return pd.DataFrame([{
        "키워드": p["keyword"], "구분": p["surface"], "광고그룹/키워드": p["name"],
        "현재순위": "미노출" if p["rank"] == 0 else p["rank"],
        "현재입찰가": p["current"], "변경입찰가": p["new"],
        "증감": p["new"] - p["current"], "ID": p["id"],
    } for p in plan])


def make_excel_bytes(results):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        result_dataframe(results).to_excel(writer, index=False, sheet_name="통합 순위")
    return output.getvalue()


def state_init():
    defaults = {"results": None, "plan": None, "stamp": None, "scan_log": "", "plan_log": "", "apply_log": "", "auth_message": "", "debug_mode": False}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


state_init()
st.title("황금이네 통합 순위체커")
st.caption("네이버 로그인 세션 재사용 + 통합검색 순위 조회 + Search AD API 승인형 5% 입찰관리")

with st.sidebar:
    st.subheader("네이버 로그인 상태")
    try:
        existing = STORE.load()
        has_auth = bool(existing)
    except Exception as e:
        existing = None
        has_auth = False
        st.error(f"인증 저장소 연결 오류: {e}")

    st.write(f"저장 방식: **{STORE.mode_name}**")
    if has_auth:
        ok, msg = validate_state_structure(existing)
        if ok:
            st.success("저장된 로그인 정보 있음")
        else:
            st.warning(msg)
    else:
        st.warning("저장된 로그인 정보 없음")

    uploaded = st.file_uploader("네이버 로그인 상태 등록", type=["json"], help="local_naver_login.py로 생성한 naver_auth_state.json을 업로드하세요.")
    if uploaded is not None:
        if st.button("업로드한 로그인 상태 저장", use_container_width=True):
            try:
                state = json.loads(uploaded.getvalue().decode("utf-8-sig"))
                ok, msg = validate_state_structure(state)
                if not ok:
                    raise ValueError(msg)
                STORE.save(state)
                st.session_state.auth_message = "네이버 로그인 상태를 저장했습니다."
                st.success(st.session_state.auth_message)
            except Exception as e:
                st.error(f"저장 실패: {e}")

    if st.button("저장된 세션 연결 확인", use_container_width=True, disabled=not has_auth):
        with st.spinner("네이버 로그인 세션을 확인하고 있습니다."):
            ok, msg = check_saved_session()
        (st.success if ok else st.error)(msg)

    if st.button("저장된 로그인 삭제", use_container_width=True, disabled=not has_auth):
        try:
            STORE.delete()
            st.success("저장된 로그인 상태를 삭제했습니다.")
            st.rerun()
        except Exception as e:
            st.error(str(e))

    if not STORE.persistent:
        st.info("현재는 로컬 파일 저장입니다. Streamlit Cloud에서 재부팅/재배포 후에도 유지하려면 README의 Supabase 설정을 추가하세요.")

    st.divider()
    st.caption("입찰 규칙")
    st.write("1위 → -5% / 2위 → 유지 / 3위 이하 → +5%")
    st.write("쇼핑 최소 50원 / 파워링크 최소 70원")
    st.write(f"프로그램 상한 {core.MAX_BID:,}원")

st.subheader("1. 순위 조회")
mode = st.radio("키워드 선택", ["전체 키워드", "직접 선택", "직접 입력"], horizontal=True)
if mode == "전체 키워드":
    selected_keywords = list(core.KEYWORDS)
elif mode == "직접 선택":
    selected_keywords = st.multiselect("조회할 키워드", core.KEYWORDS, default=core.KEYWORDS[:5])
else:
    raw = st.text_area("쉼표 또는 줄바꿈으로 입력", placeholder="흑염소진액, 도라지배즙\n호박즙")
    selected_keywords = list(dict.fromkeys(core.clean(k) for k in raw.replace("\n", ",").split(",") if core.clean(k)))

c1, c2 = st.columns(2)
with c1:
    keyword_delay = st.number_input("키워드 조회 간격(초)", min_value=0.0, max_value=30.0, value=float(core.BETWEEN_KEYWORD_SECONDS), step=0.5)
with c2:
    device_delay = st.number_input("PC → Mobile 전환 대기(초)", min_value=0.0, max_value=120.0, value=float(core.BETWEEN_DEVICE_BATCH_SECONDS), step=5.0)

st.session_state.debug_mode = st.checkbox(
    "디버그 모드 (서버가 실제로 본 검색화면과 감지 판매자 확인)",
    value=bool(st.session_state.debug_mode),
    help="문제 확인용입니다. 조회한 각 키워드의 검색결과 화면을 캡처하고 감지된 판매자명을 로그에 표시합니다.",
)

if st.button("순위 조회 시작", type="primary", disabled=not selected_keywords):
    core.BETWEEN_KEYWORD_SECONDS = float(keyword_delay)
    core.BETWEEN_DEVICE_BATCH_SECONDS = float(device_delay)
    core.DEBUG_CAPTURE_ALL = bool(st.session_state.debug_mode)
    st.session_state.plan = None
    log_box = st.empty(); logger = LiveLog(log_box)
    try:
        materialize_auth()
        with st.spinner("저장된 네이버 로그인 세션으로 순위를 조회하고 있습니다."), redirect_stdout(logger):
            results = core.collect(selected_keywords)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        core.save_results(results, stamp)
        st.session_state.results, st.session_state.stamp = results, stamp
        st.session_state.scan_log = logger.getvalue()
        st.success(f"순위 조회 완료: {len(results)}개 키워드")
    except Exception as e:
        st.session_state.scan_log = logger.getvalue()
        message = str(e)
        st.error(message)
        if "로그인" in message or "세션" in message or "NID_" in message:
            st.warning("네이버 세션이 만료된 경우 로컬에서 local_naver_login.py를 다시 실행한 뒤 새 JSON을 업로드하세요.")

if st.session_state.results:
    st.dataframe(result_dataframe(st.session_state.results), use_container_width=True, hide_index=True)
    st.download_button("순위 결과 Excel 다운로드", data=make_excel_bytes(st.session_state.results), file_name=f"황금이네_통합순위_{st.session_state.stamp}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with st.expander("조회 로그"):
        st.code(st.session_state.scan_log or "로그 없음", language=None)

    if st.session_state.debug_mode:
        st.markdown("#### 서버 검색화면 진단")
        st.caption("아래 이미지는 Streamlit 서버의 Chromium이 실제로 본 화면입니다. 로그인/검색결과/광고 노출 차이를 여기서 확인할 수 있습니다.")
        shown = set()
        for row in st.session_state.results:
            for surface, result in row.get("surfaces", {}).items():
                cap = (result or {}).get("debug_capture") or {}
                png = cap.get("png")
                if png and png not in shown and Path(png).exists():
                    shown.add(png)
                    st.markdown(f"**{row['keyword']} · {'Mobile' if 'Mobile' in surface else 'PC'}**")
                    st.image(png, use_container_width=True)
                    html = cap.get("html")
                    if html and Path(html).exists():
                        st.download_button(
                            f"{row['keyword']} HTML 진단파일 다운로드",
                            data=Path(html).read_bytes(),
                            file_name=Path(html).name,
                            mime="text/html",
                            key=f"dbg_{len(shown)}",
                        )

st.subheader("2. 입찰 변경 계획")
if not st.session_state.results:
    st.info("먼저 순위 조회를 완료하세요.")
else:
    excluded = st.multiselect("입찰 변경 제외 키워드", [r["keyword"] for r in st.session_state.results])
    allow_absent = st.checkbox("미노출 확인 항목도 +5% 인상", value=False)
    if st.button("현재 입찰가 조회 및 변경 계획 생성"):
        log_box = st.empty(); logger = LiveLog(log_box)
        try:
            with st.spinner("Search AD API에서 현재 설정을 검증하고 있습니다."), redirect_stdout(logger):
                mapping = core.load_mapping(); api = core.API()
                plan = core.build_plan(api, st.session_state.results, mapping, set(excluded), allow_absent=allow_absent)
            st.session_state.plan, st.session_state.plan_log = plan, logger.getvalue()
            if st.session_state.stamp:
                core.save_json(RESULT_DIR / f"입찰변경계획_{st.session_state.stamp}.json", plan)
            st.success(f"계획 생성 완료: 총 {len(plan)}개 검토 / 실제 변경 {sum(p['new'] != p['current'] for p in plan)}개")
        except Exception as e:
            st.session_state.plan_log = logger.getvalue(); st.error(str(e))

if st.session_state.plan is not None:
    plan_df = plan_dataframe(st.session_state.plan)
    if len(plan_df):
        st.dataframe(plan_df, use_container_width=True, hide_index=True, column_config={
            "현재입찰가": st.column_config.NumberColumn(format="%d원"),
            "변경입찰가": st.column_config.NumberColumn(format="%d원"),
            "증감": st.column_config.NumberColumn(format="%+d원"),
        })
    else:
        st.warning("변경 계획에 포함된 항목이 없습니다.")
    with st.expander("계획 생성 로그"):
        st.code(st.session_state.plan_log or "로그 없음", language=None)

    st.subheader("3. 실제 입찰가 적용")
    changes = [p for p in st.session_state.plan if p["new"] != p["current"]]
    st.warning(f"실제 변경 대상은 {len(changes)}개입니다. 쇼핑은 그룹 기본입찰가 변경이므로 같은 그룹에서 그룹입찰을 쓰는 다른 소재에도 영향을 줄 수 있습니다.")
    confirm = st.text_input("적용하려면 '변경'을 정확히 입력", value="")
    if st.button("입찰가 실제 변경", type="primary", disabled=(not changes or confirm != "변경")):
        log_box = st.empty(); logger = LiveLog(log_box)
        try:
            with st.spinner("입찰가를 변경하고 적용값을 재검증하고 있습니다."), redirect_stdout(logger):
                api = core.API(); core.execute_plan(api, changes)
            st.session_state.apply_log = logger.getvalue(); st.success("입찰가 변경 및 적용값 확인을 완료했습니다.")
        except Exception as e:
            st.session_state.apply_log = logger.getvalue(); st.error(str(e))
            if core.BID_REQUEST_ATTEMPTED:
                st.error("변경 요청을 시도한 항목이 있습니다. 광고주센터와 bid_history.jsonl에서 적용 여부를 확인하세요.")
    if st.session_state.apply_log:
        with st.expander("입찰 적용 로그"):
            st.code(st.session_state.apply_log, language=None)

st.divider()
st.caption("CAPTCHA·보호조치·보안확인 페이지는 우회하지 않고 즉시 중단합니다. 네이버가 세션을 만료시키면 다시 로그인 상태를 등록해야 합니다.")
