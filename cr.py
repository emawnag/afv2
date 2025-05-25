import requests
from bs4 import BeautifulSoup

URL = "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0040001"

session = requests.Session()
res = session.get(URL)
soup = BeautifulSoup(res.text, "html.parser")

# 取得隱藏欄位
viewstate = soup.select_one("#__VIEWSTATE")["value"]
viewstategen = soup.select_one("#__VIEWSTATEGENERATOR")["value"]

# 如果要 post，可以這樣模擬
data = {
    "__VIEWSTATE": viewstate,
    "__VIEWSTATEGENERATOR": viewstategen,
    "__EVENTTARGET": "",
    "__EVENTARGUMENT": "",
    # 加上其他必要欄位，如表單查詢時的關鍵字等
}

# 提交表單（如果有的話）
# post_res = session.post(URL, data=data)

# 這裡直接取內容
article_soup = BeautifulSoup(res.text, "html.parser")
articles = article_soup.select(".law-article .line-0000")

for article in articles:
    print(article.get_text(strip=True))
