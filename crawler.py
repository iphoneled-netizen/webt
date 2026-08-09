import requests
from bs4 import BeautifulSoup
import re

# 크롤링할 대상 URL
URL = "https://www.torrentzoa.com/board.php?mode=lists&b_id=tent&page=1"
# 차단을 막기 위해 일반 브라우저처럼 보이게 하는 헤더
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def crawl_and_generate_html():
    response = requests.get(URL, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 게시판 리스트 추출 (사이트 HTML 구조에 따라 선택자 변경 필요)
    items = []
    # 보통 게시판의 제목은 <a> 태그 안에 있습니다. 
    # (실제 사이트의 태그 구조에 맞게 a 태그를 찾는 로직입니다)
    for a_tag in soup.select('td.subject a, td.title a, a'): 
        title_text = a_tag.text.strip()
        link = a_tag.get('href', '#')
        
        # [방영중] 형수다2.E24.260809... 형태에서 '형수다2.E24'만 추출하는 정규식
        match = re.search(r'(?:\[.*?\])?\s*(.*?\.E\d+)', title_text)
        if match:
            clean_title = match.group(1).strip()
            # 중복 제거 및 리스트 추가
            if not any(item['title'] == clean_title for item in items):
                items.append({'title': clean_title, 'link': link})
                
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
</head>
<body>
"""
    # 10개씩 묶어서 HTML 문자열 만들기
    for i in range(0, len(items), 10):
        chunk = items[i:i+10]
        start_num = i + 1
        end_num = i + len(chunk)
        
        html_content += f"    <h2>{start_num}~{end_num}</h2>\n    <ul>\n"
        for item in chunk:
            html_content += f"        <li><a href='{item['link']}'>{item['title']}</a></li>\n"
        html_content += "    </ul>\n\n"

    html_content += "</body>\n</html>"

    # index.html 파일로 저장
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print("HTML 파일 생성 완료!")

if __name__ == "__main__":
    crawl_and_generate_html()
