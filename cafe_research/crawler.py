"""Navigation, search result collection, and post extraction."""

import re
from urllib.parse import parse_qs, quote, quote_plus, urljoin, urlparse
from playwright.sync_api import Frame, Page
from .models import CafeComment, CafePost

def normalize_post_url(url: str) -> str:
    parsed = urlparse(url)
    if re.search(r"/f-e/cafes/\d+/articles/\d+", parsed.path):
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    query = parse_qs(parsed.query)
    club_id = (query.get("clubid") or query.get("clubId") or [""])[0]
    article_id = (query.get("articleid") or query.get("articleId") or [""])[0]
    if club_id and article_id:
        return f"https://cafe.naver.com/ArticleRead.nhn?clubid={club_id}&articleid={article_id}"
    return url.split("#")[0]

def resolve_cafe(page: Page, cafe_url: str) -> tuple[str, str]:
    page.goto(cafe_url, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(2_000)
    path = urlparse(page.url).path
    modern = re.search(r"/f-e/cafes/(\d+)", path)
    cafe_id = modern.group(1) if modern else path.strip("/").split("/")[0]
    patterns = (r"clubid\s*[=:]\s*['\"]?(\d+)", r"clubId\s*[=:]\s*['\"]?(\d+)",
                r"search\.clubid=(\d+)")
    club_id = next((match.group(1) for pattern in patterns
                    if (match := re.search(pattern, page.content(), re.I))), "")
    if not cafe_id:
        raise RuntimeError("카페 URL에서 카페 ID를 확인하지 못했습니다.")
    return cafe_id, club_id

def _content_frame(page: Page) -> Frame:
    return page.frame(name="cafe_main") or page.main_frame

def _search_url(cafe_id: str, club_id: str, query: str) -> str:
    if cafe_id.isdigit():
        return (f"https://cafe.naver.com/f-e/cafes/{cafe_id}/menus/0"
                f"?viewType=L&ta=ARTICLE_COMMENT&q={quote_plus(query)}&page=1")
    path = f"/ArticleSearchList.nhn?search.clubid={club_id}&search.query={quote(query)}"
    return f"https://cafe.naver.com/{cafe_id}?iframe_url={quote(path, safe='')}"

def collect_search_results(page: Page, cafe_id: str, club_id: str,
                           query: str, limit: int) -> list[CafePost]:
    page.goto(_search_url(cafe_id, club_id, query), wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(3_000)
    links = _content_frame(page).locator(
        "a.article, a.article-board, a[href*='ArticleRead'], a[href*='/articles/']")
    posts, seen = [], set()
    for link in links.all():
        try:
            title = " ".join(link.inner_text(timeout=1_000).split())
            href = link.get_attribute("href") or ""
        except Exception:
            continue
        navigation_url = urljoin("https://cafe.naver.com", href)
        stable_url = normalize_post_url(navigation_url)
        if not title or not href or stable_url in seen:
            continue
        seen.add(stable_url)
        # Keep the signed in-cafe search URL until extraction is complete.
        posts.append(CafePost(title=title, url=navigation_url))
        if len(posts) >= limit:
            break
    if not posts:
        raise RuntimeError("검색 결과가 없습니다. 가입 상태와 검색어를 확인하세요.")
    return posts

def _first_text(frame: Frame, selectors: str) -> str:
    for selector in selectors.split(","):
        item = frame.locator(selector.strip()).first
        try:
            if item.count():
                text = "\n".join(line.strip() for line in item.inner_text(timeout=2_000).splitlines() if line.strip())
                if text:
                    return text
        except Exception:
            pass
    return ""

def extract_post(page: Page, post: CafePost) -> CafePost:
    page.goto(post.url, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(1_500)
    frame = _content_frame(page)
    post.title = _first_text(frame, ".ArticleTitle .title_text, .article_title, h3") or post.title
    post.text = _first_text(frame, ".se-main-container, .ContentRenderer, .article_viewer, #tbody")
    post.author = _first_text(frame, ".nickname, .WriterInfo .nick, .p-nick")
    post.date = _first_text(frame, ".date, .ArticleTool .date, .article_info .date")
    post.comments = extract_comments(frame)
    post.url = normalize_post_url(post.url)
    return post

def _item_text(item, selector: str) -> str:
    target = item.locator(selector).first
    try:
        return " ".join(target.inner_text(timeout=1_000).split()) if target.count() else ""
    except Exception:
        return ""

def extract_comments(frame: Frame) -> list[CafeComment]:
    try:
        frame.locator(".CommentItem").first.wait_for(state="attached", timeout=7_000)
    except Exception:
        return []
    comments = []
    for item in frame.locator(".CommentItem").all():
        text = _item_text(item, ".text_comment")
        if not text:
            continue
        classes = item.get_attribute("class") or ""
        comments.append(CafeComment(
            author=_item_text(item, ".comment_nickname"),
            text=text,
            date=_item_text(item, ".comment_info_date"),
            is_reply="CommentItem--reply" in classes,
        ))
    return comments

def extract_all(page: Page, posts: list[CafePost]) -> list[CafePost]:
    extracted = []
    for index, post in enumerate(posts, 1):
        print(f"[{index}/{len(posts)}] {post.title}")
        try:
            extracted.append(extract_post(page, post))
        except Exception as exc:
            print(f"  건너뜀: {exc}")
    return extracted
