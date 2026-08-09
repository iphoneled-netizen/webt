import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from html import escape

# 크롤링할 대상 URL
URL = "https://www.torrentzoa.com/board.php?mode=lists&b_id=tent"

# 일반 브라우저처럼 보이게 하는 헤더
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
}


def clean_title(title_text):
    """
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


def make_item(a_tag):
    """
    a 태그에서 제목과 절대 URL을 추출
    """

    title_text = a_tag.get_text(" ", strip=True)
    href = a_tag.get("href")

    if not href:
        return None

    clean = clean_title(title_text)

    if not clean:
        return None

    # 상대주소 -> 원본 사이트 절대주소
    full_url = urljoin(URL, href)

    return {
        "title": clean,
        "link": full_url
    }


def crawl_and_generate_html():

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

    # =========================================================
    # 1. 베스트 추출
    # =========================================================

    best_items = []

    # 현재 사이트는
    # 일간 베스트 5개
    # 주간 베스트 5개
    # 구조로 되어 있음
    #
    # "일간 베스트"와 "주간 베스트" 사이 및
    # "주간 베스트" 다음의 링크를 찾아서 추출

    best_headings = soup.find_all(
        string=lambda text:
        text and text.strip() in ["일간 베스트", "주간 베스트"]
    )

    for heading in best_headings:

        # heading이 들어있는 부모 영역
        parent = heading.parent

        # 부모 영역 안의 a 태그 탐색
        for a_tag in parent.find_all("a"):
            item = make_item(a_tag)

            if item:
                # 중복 제거
                if not any(
                    x["title"] == item["title"]
                    for x in best_items
                ):
                    best_items.append(item)

    # 위 방식으로 부모에서 못 찾는 경우를 대비해서
    # 페이지 전체에서 베스트 제목들을 직접 찾음
    if len(best_items) < 9:

        all_links = soup.find_all("a")

        best_started = False

        for a_tag in all_links:

            text = a_tag.get_text(" ", strip=True)

            if text == "일간 베스트":
                best_started = True
                continue

            if text == "주간 베스트":
                best_started = True
                continue

            if best_started:
                item = make_item(a_tag)

                if item:
                    if not any(
                        x["title"] == item["title"]
                        for x in best_items
                    ):
                        best_items.append(item)

                if len(best_items) >= 10:
                    break

    # 베스트는 정확히 9개
    best_items = best_items[:9]

    # =========================================================
    # 2. 최신 등록 목록 추출
    # =========================================================

    latest_items = []

    # 베스트에서 사용된 제목
    # 최신 목록과 겹치는 경우 제거하기 위해 저장
    best_titles = {
        item["title"]
        for item in best_items
    }

    # 게시판의 실제 게시물 링크 찾기
    #
    # 현재 페이지에서 게시물은
    # 27648
    # 27647
    # 27646
    # ...
    # 순서로 최신순 정렬되어 있음.
    #
    # 제목에 .E숫자가 포함된 링크만 가져옴.

    for a_tag in soup.find_all("a"):

        item = make_item(a_tag)

        if not item:
            continue

        # 베스트와 중복되는 항목도 최신 목록에서는
        # 그대로 보여주고 싶다면 이 부분을 삭제하면 됨.
        #
        # 여기서는 "최신 등록 목록"을 원본 게시판 그대로
        # 보여주기 위해 중복도 포함시킴.

        if not any(
            x["title"] == item["title"]
            for x in latest_items
        ):
            latest_items.append(item)

    # =========================================================
    # 3. 베스트 링크가 최신 목록에 섞이는 문제 방지
    # =========================================================

    # 베스트는 페이지 상단에 있으므로
    # 최신 목록을 찾을 때 처음 9개를 제외하는 방식이 아니라
    # 게시물 영역을 기준으로 다시 추출

    latest_items = []

    # "No 제목 날자"가 들어있는 영역을 찾음
    board_header = soup.find(
        string=lambda text:
        text and "No" in text and "제목" in text and "날자" in text
    )

    if board_header:

        # 게시판 헤더가 속한 테이블을 찾음
        board_table = board_header.find_parent("table")

        if board_table:

            for a_tag in board_table.find_all("a"):

                item = make_item(a_tag)

                if not item:
                    continue

                if not any(
                    x["title"] == item["title"]
                    for x in latest_items
                ):
                    latest_items.append(item)

    # 테이블 선택이 안 되는 사이트 구조일 경우
    # 전체 링크에서 게시물 번호 영역 이후를 대체하는 방식
    if not latest_items:

        # 현재 페이지의 게시물 번호를 기준으로 추출
        for a_tag in soup.find_all("a"):

            href = a_tag.get("href", "")
            title_text = a_tag.get_text(" ", strip=True)

            # 게시물 상세 링크인지 확인
            if "board.php" not in href:
                continue

            if "mode=view" not in href:
                continue

            item = make_item(a_tag)

            if item:
                if not any(
                    x["title"] == item["title"]
                    for x in latest_items
                ):
                    latest_items.append(item)

    # 최신 목록 최대 35개
    latest_items = latest_items[:35]

    # =========================================================
    # 4. HTML 생성
    # =========================================================

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
            font-family:
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Arial,
                sans-serif;

            max-width: 800px;

            margin: 0 auto;

            padding: 20px;

            line-height: 1.6;

            background: #f5f5f5;
        }

        .container {
            background: white;

            padding: 20px;

            border-radius: 12px;
        }

        h1 {
            margin-top: 0;

            font-size: 24px;
        }

        h2 {
            margin-top: 30px;

            padding-bottom: 8px;

            border-bottom: 2px solid #333;
        }

        .best {
            margin-bottom: 30px;
        }

        .best li {
            font-weight: 600;
        }

        .latest li {
            margin: 7px 0;
        }

        ul {
            padding-left: 22px;
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

            background: #ddd;

            margin: 30px 0;
        }

        .update {
            color: #888;

            font-size: 13px;

            margin-top: 30px;
        }

    </style>

</head>

<body>

<div class="container">

    <h1>📺 예능 프로그램</h1>

    <section class="best">

        <h2>🔥 베스트</h2>

        <ol>
"""

    # =========================================================
    # 5. 베스트 9개 출력
    # =========================================================

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

    html_content += """
        </ol>

    </section>

    <div class="divider"></div>

    <section class="latest">

        <h2>🆕 최신 등록</h2>

        <ol>
"""

    # =========================================================
    # 6. 최신 등록 목록 출력
    # =========================================================

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

    # =========================================================
    # 7. index.html 저장
    # =========================================================

    with open(
        "index.html",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(html_content)

    # =========================================================
    # 8. 결과 확인
    # =========================================================

    print("")
    print("=" * 50)
    print("🔥 베스트")
    print("=" * 50)

    for i, item in enumerate(best_items, 1):

        print(
            f"{i}. "
            f"{item['title']} -> "
            f"{item['link']}"
        )

    print("")
    print("=" * 50)
    print("🆕 최신 등록")
    print("=" * 50)

    for i, item in enumerate(latest_items, 1):

        print(
            f"{i}. "
            f"{item['title']} -> "
            f"{item['link']}"
        )

    print("")
    print(
        f"베스트 {len(best_items)}개 / "
        f"최신 {len(latest_items)}개"
    )

    print("")
    print("HTML 파일 생성 완료!")


if __name__ == "__main__":
    crawl_and_generate_html()
