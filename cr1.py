import requests
from bs4 import BeautifulSoup
import re

# 多條法規的 URL 列表
law_sources = {
    "食品安全衛生管理法": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0040001",
    "藥事法": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0030001",
    "化粧品衛生安全管理法": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0030013",
    "醫療器材管理法": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0030106"
}

# 清理條文用的工具
def clean_text(text):
    text = re.sub(r'\u3000+', ' ', text)  # 全形空格處理
    return re.sub(r'\s+', ' ', text).strip()

# 單條法規的爬蟲邏輯
def crawl_law(url, law_name):
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")

    content = []
    current_chapter = ""

    # 使用表格方式解析
    for row in soup.select("div.law-reg-content .row"):
        article_tag = row.select_one(".col-no a")
        text_tag = row.select_one(".col-data .law-article")
        if not article_tag or not text_tag:
            continue

        article_number = article_tag.get_text(strip=True)
        full_text = clean_text(text_tag.get_text(separator=" ", strip=True))

        # 若前面是章節標題
        chapter_tag = row.find_previous("div", class_="h3 char-2")
        if chapter_tag:
            current_chapter = clean_text(chapter_tag.get_text())

        content.append({
            "法規": law_name,
            "章節": current_chapter,
            "條號": article_number,
            "條文": full_text
        })

    return content

# 處理多個法規
all_laws = []
for name, url in law_sources.items():
    print(f"正在爬取：{name}")
    law_data = crawl_law(url, name)
    all_laws.extend(law_data)

# 示範輸出前 3 筆
for item in all_laws[:3]:
    print(item)
