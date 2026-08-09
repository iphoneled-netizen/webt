import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from html import escape


# =========================================================
# 설정
# =========================================================

URL = "https://www.torrentzoa.com/board.php?mode=lists&b_id=tent"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
}

# 베스트 개수
BEST_COUNT = 9

# 최신 등록 개수
LATEST_COUNT = 35


# =========================================================
# 제목 정리
# =========================================================

def clean_title(title_text):

    """
    예:

    [방영중] 형수다2.E24.260809.720p-NEXT
    ->
    형수다2.E24
    """

    match = re.search(
        r"(?:\[.*?\])?\s*(.*?\.E\d+)",
        title_text
    )

    if match:
        return match.group(1).strip()

    return None


# =========================================================
# 게시물 정보 추출
# =========================================================

def make_item(a_tag):

    title_text = a_tag.get_text(" ", strip=True)

    href = a_tag.get("href")

    if not href:
        return None

    # 제목 정리
    clean = clean_title(title_text)

    if not clean:
        return None

    # 상대주소를 원본 사이트 절대주소로 변경
    full_url = urljoin(URL, href)

    return {
        "title": clean,
        "link": full_url
    }


# =========================================================
# 크롤링
# =========================================================

def crawl_and_generate_html():

    print("크롤링 시작...")
    print(URL)

    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    # =====================================================
    # 페이지에서 게시물 전체 추출
    # =====================================================

    all_items = []

    for a_tag in soup.find_all("a"):

        item = make_item(a_tag)

        if not item:
            continue

        # 중복 제거
        if any(
            x["title"] == item["title"]
            for x in all_items
        ):
            continue

        all_items.append(item)

    print("")
    print(f"찾은 게시물: {len(all_items)}개")


    # =====================================================
    # 1~9번 = 베스트
    # =====================================================

    best_items = all_items[:BEST_COUNT]


    # =====================================================
    # 10번부터 = 최신 등록
    # =====================================================

    latest_items = all_items[BEST_COUNT:BEST_COUNT + LATEST_COUNT]


    # =====================================================
    # HTML 시작
    # =====================================================

    html_content = """<!DOCTYPE html>
<html lang="ko">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>예능 프로그램 리스트</title>

    <style>

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 20px;

            background: #f5f5f5;

            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Arial,
                sans-serif;

            line-height: 1.6;
        }

        .container {
            max-width: 800px;

            margin: 0 auto;

            background: #ffffff;

            padding: 20px;

            border-radius: 12px;

            box-shadow:
                0 2px 10px rgba(0, 0, 0, 0.05);
        }

        h1 {
            margin-top: 0;

            margin-bottom: 25px;

            font-size: 24px;
        }

        h2 {
            margin-top: 25px;

            padding-bottom: 10px;

            border-bottom: 2px solid #333;

            font-size: 20px;
        }

        ol {
            padding-left: 25px;
        }

        li {
            margin: 8px 0;
        }

        .best li {
            font-weight: 600;
        }

        .latest li {
            font-weight: 400;
        }

        a {
            color: #0066cc;

            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }

        .divider {
            height: 1px;

            background: #dddddd;

            margin: 30px 0;
        }

        .update {
            margin-top: 30px;

            color: #999999;

            font-size: 13px;

            text-align: center;
        }

    </style>

</head>

<body>

<div class="container">

    <h1>📺 예능 프로그램</h1>


    <!-- =================================================
         베스트
         ================================================= -->

    <section class="best">

        <h2>🔥 베스트</h2>

        <ol>
"""


    # =====================================================
    # 베스트 9개 출력
    # =====================================================

    for item in best_items:

        title = escape(item["title"])

        link = escape(
            item["link"],
            quote=True
        )

        html_content += (
            f'            <li>'
            f'<a href="{link}" '
            f'target="_blank" '
            f'rel="noopener noreferrer">'
            f'{title}'
            f'</a>'
            f'</li>\n'
        )


    # =====================================================
    # 최신 등록 영역
    # =====================================================

    html_content += """
        </ol>

    </section>


    <div class="divider"></div>


    <!-- =================================================
         최신 등록
         ================================================= -->

    <section class="latest">

        <h2>🆕 최신 등록</h2>

        <ol>
"""


    # =====================================================
    # 최신 등록 출력
    # =====================================================

    for item in latest_items:

        title = escape(item["title"])

        link = escape(
            item["link"],
            quote=True
        )

        html_content += (
            f'            <li>'
            f'<a href="{link}" '
            f'target="_blank" '
            f'rel="noopener noreferrer">'
            f'{title}'
            f'</a>'
            f'</li>\n'
        )


    # =====================================================
    # HTML 종료
    # =====================================================

    html_content += """
        </ol>

    </section>


    <div class="update">
        자동 업데이트
    </div>

</div>

</body>

</html>
"""


    # =====================================================
    # index.html 저장
    # =====================================================

    with open(
        "index.html",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(html_content)


    # =====================================================
    # 결과 출력
    # =====================================================

    print("")
    print("=" * 60)

    print("🔥 베스트")
    print("=" * 60)

    for i, item in enumerate(best_items, 1):

        print(
            f"{i}. "
            f"{item['title']}"
        )


    print("")
    print("=" * 60)

    print("🆕 최신 등록")
    print("=" * 60)

    for i, item in enumerate(latest_items, 10):

        print(
            f"{i}. "
            f"{item['title']}"
        )


    print("")
    print("=" * 60)

    print(
        f"베스트: {len(best_items)}개"
    )

    print(
        f"최신 등록: {len(latest_items)}개"
    )

    print("=" * 60)

    print("")
    print("index.html 생성 완료!")


# =========================================================
# 실행
# =========================================================

if __name__ == "__main__":
    crawl_and_generate_html()
