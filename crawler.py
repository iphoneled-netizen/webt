import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from html import escape

# 크롤링할 대상 URL
URL = "https://www.torrentzoa.com/board.php?mode=lists&b_id=tent&page=1"

# 차단을 막기 위해 일반 브라우저처럼 보이게 하는 헤더
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
}


def crawl_and_generate_html():
    response = requests.get(URL, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # 게시판 리스트 추출
    items = []

    for a_tag in soup.select("td.subject a, td.title a, a"):
        title_text = a_tag.get_text(" ", strip=True)

        # href 가져오기
        link = a_tag.get("href")

        if not link:
            continue

        # 상대경로를 원본 사이트의 절대 URL로 변환
        link = urljoin(URL, link)

        # [방영중] 형수다2.E24.260809... 형태에서
        # 형수다2.E24 부분만 추출
        match = re.search(
            r"(?:\[.*?\])?\s*(.*?\.E\d+)",
            title_text
        )

        if match:
            clean_title = match.group(1).strip()

            # 중복 제거
            if not any(item["title"] == clean_title for item in items):
                items.append({
                    "title": clean_title,
                    "link": link
                })

        # 35개까지만 추출
        if len(items) >= 35:
            break

    # HTML 생성
    html_content = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>예능 프로그램 리스트</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }

        h1 {
            margin-bottom: 30px;
        }

        h2 {
            margin-top: 25px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 8px;
        }

        ul {
            padding-left: 20px;
        }

        li {
            margin: 8px 0;
        }

        a {
            color: #0066cc;
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>

<h1>예능 프로그램 리스트</h1>
"""

    # 10개씩 묶어서 HTML 생성
    for i in range(0, len(items), 10):
        chunk = items[i:i + 10]

        start_num = i + 1
        end_num = i + len(chunk)

        html_content += (
            f"    <h2>{start_num}~{end_num}</h2>\n"
            "    <ul>\n"
        )

        for item in chunk:
            title = escape(item["title"])
            link = escape(item["link"], quote=True)

            html_content += (
                f'        <li><a href="{link}" '
                f'target="_blank" rel="noopener noreferrer">'
                f"{title}</a></li>\n"
            )

        html_content += "    </ul>\n\n"

    html_content += """
</body>
</html>
"""

    # index.html 파일로 저장
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"HTML 파일 생성 완료! 총 {len(items)}개")

    # 생성된 링크 확인
    for item in items:
        print(f"{item['title']} -> {item['link']}")


if __name__ == "__main__":
    crawl_and_generate_html()
