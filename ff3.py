from rag_library import RAGWithCitations
import pandas as pd
import mysql.connector

# ---------------------
# 系統提示
# ---------------------
system_prompt = """## 目標
分析廣告文字內容，根據法律條款和案例判斷廣告用詞是否涉及誇大療效及違法，並提供違法機率評估。回應內容必須完全依照格式，且使用繁體中文。回應簡潔有力，不需要提供分析過程的文字。

### 合規性判斷
- **無罪判定原則**：不捏造或過度解讀廣告文字，**從寬認定合法性**，但如果是**藥物**宣稱**科學實證**、**國外研究**一類用語，則提高違法可能性認定，除非內容中出現完整的**衛福部核可字號**或**衛福部認證**。
- **比對允許使用的廣告用詞**：
  - 「完整補充營養」「調整體質」「促進新陳代謝」「幫助入睡」「保護消化道全機能」「改變細菌叢生態」「排便有感」「在嚴謹的營養均衡與熱量控制，以及適當的運動條件下，適量攝取本產品有助於不易形成體脂肪」這些文字出現時不視為有違法風險。
 - 「能完整補充人體營養」、「調整體質」、「提升生理機能」、「調節生理機能」、「促進新陳代謝」、「幫助入睡」、「調整體質」、「青春美麗」、「排便超有感」、「給你排便順暢新體驗」、「維持正常的排便習慣」、「排便順暢」、「促進新陳代謝」、「調整體質」、「改變細菌叢生態」、調節生理機能」、「保護消化道全機能」、「提升吸收滋養消化機能」這些文字出現時不視為有違法風險。

## 分析步驟
1. **解析廣告內容**
2. **引用法條（由系統自動比對）**
3. **輸出判定（T=違法風險高，F=風險低）**
"""

# ---------------------
# 初始化 RAG 模型
# ---------------------
rag = RAGWithCitations("PleIAs/Pleias-RAG-1B", system_prompt=system_prompt)

# ---------------------
# MySQL 法條資料載入
# ---------------------
db = mysql.connector.connect(
    host="localhost",
    user="andyuser",
    password="adminpsw",
    database="ai_db"
)
cursor = db.cursor(dictionary=True)
cursor.execute("SELECT id, content FROM laws")
laws = cursor.fetchall()

sources = [
    {
        "text": law["content"],
        "metadata": {"id": law["id"]}
    }
    for law in laws
]

# ---------------------
# 讀取 Query CSV
# ---------------------
query_df = pd.read_csv("the_query.csv")
results = []

# ---------------------
# 執行每筆判定
# ---------------------
for i, row in query_df.iterrows():
    query = row["Question"]
    response = rag.generate(query, sources)

    raw_answer = response["processed"]["clean_answer"]
    label = 0 if raw_answer.startswith("T") else 1  # T=違法（0）, F=合規（1）

    results.append({
        "ID": i,
        "Label": label,
        "Answer": raw_answer,
        "Citations": ";".join([str(c) for c in response.get("citations", [])])
    })

# ---------------------
# 輸出結果
# ---------------------
out_df = pd.DataFrame(results)
out_df.to_csv("tf_results.csv", index=False)
print("✅ 已輸出結果到 tf_results.csv")
