"""AI-based relevance filtering and report generation."""

from openai import OpenAI
from .models import CafePost

def usable_posts(posts: list[CafePost]) -> list[CafePost]:
    return [post for post in posts if len(post.text) >= 80]

def _source_text(posts: list[CafePost]) -> str:
    return "\n\n".join(
        f"[글 {i}]\n제목: {post.title}\nURL: {post.url}\n작성일: {post.date}\n본문:\n{post.text[:8000]}"
        for i, post in enumerate(posts, 1))

def _prompt(query: str, posts: list[CafePost]) -> str:
    return f"""사용자의 조사 주제는 '{query}'입니다.
아래 네이버 카페 글만 근거로 한국어 조사 보고서를 작성하세요.

1. 광고, 인사, 중복, 근거 없는 짧은 주장은 제외
2. 핵심 주제와 합의/이견을 요약
3. 활용 가능한 정보, 팁, 수치, 주의점을 추출
4. 'AI의 의견'에서 사실과 추론을 구분하고 자료의 한계를 제시
5. 마지막에 제공된 URL만 이용한 '주요 글 URL' 목록 작성
6. 근거가 부족한 내용은 만들어내지 말고 명시

자료:
{_source_text(posts)}"""

def analyze_posts(query: str, posts: list[CafePost], model: str) -> str:
    posts = usable_posts(posts)
    if not posts:
        raise RuntimeError("분석 가능한 본문이 없습니다. 읽기 권한을 확인하세요.")
    return OpenAI().responses.create(model=model, input=_prompt(query, posts)).output_text.strip()
