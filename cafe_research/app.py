"""Application workflow for a cafe research run."""

from argparse import Namespace
from playwright.sync_api import sync_playwright
from lib.browser_session import has_naver_login, open_browser_session, save_debug_artifacts, wait_for_naver_login
from .analyzer import analyze_posts
from .config import ARTIFACTS_DIR, OUTPUT_DIR, PROFILE_DIR, READY_MARKER
from .crawler import collect_search_results, extract_all, resolve_cafe
from .output import write_results

def research(page, cafe_url: str, query: str, limit: int, model: str,
             collect_only: bool = False):
    cafe_id, club_id = resolve_cafe(page, cafe_url)
    results = collect_search_results(page, cafe_id, club_id, query, limit)
    posts = extract_all(page, results)
    report = ("## 수집 전용 결과\n\nAI 분석 없이 원본 게시글만 수집했습니다."
              if collect_only else analyze_posts(query, posts, model))
    return write_results(OUTPUT_DIR, query, cafe_url, posts, report)

def run(args: Namespace) -> int:
    with sync_playwright() as playwright:
        session = open_browser_session(playwright, PROFILE_DIR,
                                       headed=args.setup or args.headed,
                                       cdp_url=args.cdp_url)
        try:
            if args.setup:
                wait_for_naver_login(session, READY_MARKER, args.setup_timeout)
                return 0
            if not has_naver_login(session.context):
                raise RuntimeError("네이버 로그인이 없습니다. 먼저 .\\run.ps1 --setup을 실행하세요.")
            markdown, raw_data = research(session.page, args.cafe_url, args.query,
                                          args.limit, args.model, args.collect_only)
            print(f"보고서: {markdown}\n원본 데이터: {raw_data}")
            return 0
        except Exception as exc:
            save_debug_artifacts(session.page, ARTIFACTS_DIR)
            print(f"오류: {exc}")
            return 1
        finally:
            session.close()
