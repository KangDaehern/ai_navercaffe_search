"""Reusable Chrome session management for Naver automation."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from playwright.sync_api import Browser, BrowserContext, Page, Playwright


NAVER_LOGIN_COOKIES = {"NID_AUT", "NID_SES"}


@dataclass
class BrowserSession:
    context: BrowserContext
    page: Page
    browser: Browser | None = None
    attached: bool = False

    def close(self) -> None:
        # An attached Chrome belongs to the user; close only our tab. Persistent
        # contexts launched by us are closed normally so cookies are flushed.
        if self.attached:
            # browser.close() would also close the user's Chrome over CDP.
            # Only close the tab created for this research run.
            self.page.close()
        else:
            self.context.close()


def has_naver_login(context: BrowserContext) -> bool:
    names = {cookie["name"] for cookie in context.cookies("https://naver.com")}
    return bool(names & NAVER_LOGIN_COOKIES)


def open_browser_session(
    playwright: Playwright,
    profile_dir: Path,
    *,
    headed: bool = True,
    cdp_url: str | None = None,
) -> BrowserSession:
    """Attach to a debugging-enabled Chrome, or use our persistent profile.

    Chrome cannot safely expose an already-running normal profile to Playwright.
    If Chrome was started with ``--remote-debugging-port=9222``, passing its CDP
    URL reuses that exact logged-in session. Otherwise a dedicated persistent
    profile is used and retains cookies between runs.
    """
    if cdp_url:
        try:
            browser = playwright.chromium.connect_over_cdp(cdp_url, timeout=8_000)
            contexts = browser.contexts
            if contexts:
                context = contexts[0]
                page = context.new_page()
                return BrowserSession(context, page, browser=browser, attached=True)
            browser.close()
        except Exception as exc:
            print(f"기존 Chrome 연결 실패, 전용 프로필을 사용합니다: {exc}")

    profile_dir.mkdir(parents=True, exist_ok=True)
    context = playwright.chromium.launch_persistent_context(
        str(profile_dir),
        channel="chrome",
        headless=not headed,
        args=["--profile-directory=Default", "--no-first-run"],
        viewport={"width": 1600, "height": 1000},
        timeout=60_000,
    )
    page = context.pages[0] if context.pages else context.new_page()
    return BrowserSession(context, page)


def wait_for_naver_login(
    session: BrowserSession, marker_path: Path, timeout_seconds: int = 600
) -> None:
    session.page.goto("https://nid.naver.com/nidlogin.login", wait_until="domcontentloaded")
    print("열린 Chrome 창에서 네이버 로그인을 완료해 주세요.", flush=True)
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if has_naver_login(session.context):
            marker_path.parent.mkdir(parents=True, exist_ok=True)
            marker_path.write_text(
                json.dumps({"created_at": time.strftime("%Y-%m-%d %H:%M:%S")}),
                encoding="utf-8",
            )
            print("로그인 확인 완료. 세션을 전용 프로필에 저장했습니다.")
            return
        session.page.wait_for_timeout(1_000)
    raise RuntimeError("로그인 대기 시간이 초과되었습니다. --setup을 다시 실행하세요.")


def save_debug_artifacts(page: Page, directory: Path, prefix: str = "error") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    try:
        page.screenshot(path=str(directory / f"{prefix}-{stamp}.png"), full_page=True)
        (directory / f"{prefix}-{stamp}.html").write_text(page.content(), encoding="utf-8")
    except Exception:
        pass
