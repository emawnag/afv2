import requests
from bs4 import BeautifulSoup
import re
import mysql.connector

# 資料庫連線設定
db = mysql.connector.connect(
    host="localhost",
    user="andyuser",
    password="adminpsw",
    database="ai_db"
)
cursor = db.cursor()

# 建立表格（如尚未建立）
cursor.execute("""
CREATE TABLE IF NOT EXISTS laws (
    id INT AUTO_INCREMENT PRIMARY KEY,
    law_name VARCHAR(255),
    chapter TEXT,
    article_number VARCHAR(50),
    content TEXT
)
""")

# 清理條文內容
def clean_text(text):
    text = re.sub(r'\u3000+', ' ', text)  # 全形空格處理
    return re.sub(r'\s+', ' ', text).strip()

# 爬蟲邏輯
def crawl_law(url, law_name):
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, "html.parser")

    content = []
    current_chapter = ""

    for row in soup.select("div.law-reg-content .row"):
        article_tag = row.select_one(".col-no a")
        text_tag = row.select_one(".col-data .law-article")
        if not article_tag or not text_tag:
            continue

        article_number = article_tag.get_text(strip=True)
        full_text = clean_text(text_tag.get_text(separator=" ", strip=True))

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

# 多條法規 URL
law_sources = {
    "食品安全衛生管理法": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0040001",
    "藥事法": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0030001",
    "化粧品衛生安全管理法": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0030013",
    "醫療器材管理法": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0030106"
}

# 執行爬蟲並寫入資料庫
for law_name, url in law_sources.items():
    print(f"正在爬取：{law_name}")
    data = crawl_law(url, law_name)
    for item in data:
        cursor.execute(
            "INSERT INTO laws (law_name, chapter, article_number, content) VALUES (%s, %s, %s, %s)",
            (item["法規"], item["章節"], item["條號"], item["條文"])
        )
    db.commit()

print("✅ 所有法規資料已成功寫入 MySQL 資料庫")

# 關閉連線
cursor.close()
db.close()
