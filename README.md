# Naver Cafe Researcher

지정한 네이버 카페 안에서 검색어와 관련된 글을 수집하고, 의미 없는 글을 제외한 뒤 핵심 내용·활용 정보·AI 의견을 Markdown 보고서로 만듭니다. 카페의 공개 범위와 현재 로그인 계정의 열람 권한을 그대로 따릅니다.

## 준비

PowerShell에서 최초 한 번 전용 Chrome 창을 열고 네이버에 로그인합니다. 로그인 쿠키는 Git에 포함되지 않는 `.browser-profile/`에 보존됩니다.

```powershell
cd E:\gitView\ai_navercaffe_search
.\run.ps1 --setup
```

AI 분석에는 OpenAI API 키가 필요합니다.

```powershell
$env:OPENAI_API_KEY = "your-api-key"
```

## 실행

```powershell
.\run.ps1 `
  --cafe-url "https://cafe.naver.com/example" `
  --query "검색하고 싶은 내용" `
  --limit 15
```

결과는 `output/`에 생성됩니다.

API 호출 없이 게시글 원본만 모으려면 `--collect-only`를 추가합니다. 이 모드에서는
`OPENAI_API_KEY`가 필요하지 않습니다.

- `.md`: 핵심 요약, 쓸만한 정보, 한계, AI 의견
- `.json`: 수집한 글의 제목·작성자·날짜·본문 원본과 내부 처리 정보
- 각 글의 댓글 작성자·본문·작성시각·답글 여부도 JSON과 AI 분석에 포함
- 오류가 나면 `artifacts/`에 당시 화면과 HTML 저장

브라우저 동작을 직접 보려면 `--headed`를 추가합니다. 분석 모델은 `--model` 또는 `OPENAI_MODEL`로 바꿀 수 있습니다.

## 이미 로그인한 Chrome 재사용

보통 실행 중인 Chrome에는 보안상 자동화 도구가 바로 연결될 수 없습니다. Chrome을 원격 디버깅 옵션으로 시작한 경우에만 해당 로그인 세션을 그대로 쓸 수 있습니다.

```powershell
chrome.exe --remote-debugging-port=9222
$env:CHROME_CDP_URL = "http://127.0.0.1:9222"
.\run.ps1 --cafe-url "https://cafe.naver.com/example" --query "검색어"
```

연결에 실패하면 프로그램은 자동으로 전용 `.browser-profile` Chrome을 사용합니다. 일반 Chrome 프로필 파일을 강제로 복사하지 않으므로 프로필 손상과 쿠키 유출 위험을 줄입니다.

## 주의사항

- 가입하지 않은 카페나 등급 제한 게시물은 수집할 수 없습니다.
- 네이버 화면 구조가 바뀌면 선택자 보완이 필요할 수 있으며, 이때 `artifacts/` 자료가 진단에 유용합니다.
- 과도한 요청을 피하려고 기본 수집량을 15개로 제한했습니다. 서비스 약관과 게시물 저작권·개인정보를 준수해 사용하세요.
- API 키와 `.browser-profile/`은 외부에 공유하거나 Git에 커밋하지 마세요.

## 코드 구조

- `naver_cafe_researcher.py`: CLI 인자 처리와 실행 시작점
- `cafe_research/crawler.py`: 카페 검색, 링크 수집, 본문 추출
- `cafe_research/analyzer.py`: 유효 글 선별과 AI 분석
- `cafe_research/output.py`: Markdown·JSON 결과 저장
- `cafe_research/app.py`: 각 모듈을 연결하는 실행 흐름
- `lib/browser_session.py`: 다른 네이버 자동화에서도 재사용할 브라우저 세션
