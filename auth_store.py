# -*- coding: utf-8 -*-
"""Persistent storage for Playwright/Naver authentication state.

Uses Supabase REST when configured; otherwise falls back to a local file.
The local fallback is convenient for local Streamlit, but cloud filesystem
may be reset on reboot/redeploy.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests


class AuthStore:
    def __init__(self, local_path: Path, supabase_url: str = "", supabase_key: str = "", table: str = "naver_sessions", session_key: str = "default"):
        self.local_path = Path(local_path)
        self.supabase_url = (supabase_url or "").rstrip("/")
        self.supabase_key = supabase_key or ""
        self.table = table or "naver_sessions"
        self.session_key = session_key or "default"

    @property
    def persistent(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)

    @property
    def mode_name(self) -> str:
        return "Supabase 영구 저장" if self.persistent else "로컬 파일 저장"

    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
        }

    def load(self) -> dict[str, Any] | None:
        if self.persistent:
            url = f"{self.supabase_url}/rest/v1/{self.table}"
            params = {
                "session_key": f"eq.{self.session_key}",
                "select": "auth_state",
                "limit": "1",
            }
            r = requests.get(url, headers=self._headers(), params=params, timeout=20)
            r.raise_for_status()
            rows = r.json()
            if not rows:
                return None
            state = rows[0].get("auth_state")
            return state if isinstance(state, dict) else json.loads(state)

        if not self.local_path.exists():
            return None
        return json.loads(self.local_path.read_text(encoding="utf-8"))

    def save(self, state: dict[str, Any]) -> None:
        # Always keep a working local copy for Playwright.
        self.local_path.parent.mkdir(parents=True, exist_ok=True)
        self.local_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

        if self.persistent:
            url = f"{self.supabase_url}/rest/v1/{self.table}"
            headers = self._headers()
            headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
            payload = {
                "session_key": self.session_key,
                "auth_state": state,
            }
            r = requests.post(url, headers=headers, params={"on_conflict": "session_key"}, json=payload, timeout=20)
            r.raise_for_status()

    def delete(self) -> None:
        try:
            self.local_path.unlink(missing_ok=True)
        except Exception:
            pass
        if self.persistent:
            url = f"{self.supabase_url}/rest/v1/{self.table}"
            r = requests.delete(
                url,
                headers=self._headers(),
                params={"session_key": f"eq.{self.session_key}"},
                timeout=20,
            )
            r.raise_for_status()

    def materialize(self) -> Path | None:
        state = self.load()
        if not state:
            return None
        self.local_path.parent.mkdir(parents=True, exist_ok=True)
        self.local_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return self.local_path
