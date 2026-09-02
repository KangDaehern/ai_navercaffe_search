#!/usr/bin/env python3
"""Search a Naver Cafe and create an AI research report."""

import argparse
import os
import sys
from cafe_research.app import run

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cafe-url", help="target Naver Cafe URL")
    parser.add_argument("--query", help="text to search inside the cafe")
    parser.add_argument("--limit", type=int, default=15)
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-5-mini"))
    parser.add_argument("--setup", action="store_true")
    parser.add_argument("--setup-timeout", type=int, default=600)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--cdp-url", default=os.getenv("CHROME_CDP_URL"))
    parser.add_argument("--collect-only", action="store_true",
                        help="collect posts without calling the OpenAI API")
    args = parser.parse_args()
    if not args.setup and (not args.cafe_url or not args.query):
        parser.error("--cafe-url and --query are required unless --setup is used")
    return args

def validate_environment(args: argparse.Namespace) -> bool:
    if args.setup or args.collect_only or os.getenv("OPENAI_API_KEY"):
        return True
    print("오류: OPENAI_API_KEY 환경 변수가 필요합니다.", file=sys.stderr)
    return False

def main() -> int:
    args = parse_args()
    return run(args) if validate_environment(args) else 2

if __name__ == "__main__":
    raise SystemExit(main())
