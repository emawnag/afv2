import pandas as pd
import mysql.connector
import numpy as np
from sentence_transformers import SentenceTransformer
from rag_library import RAGWithCitations
import json

# ---------------------
# 初始化模型
# ---------------------
embedder = SentenceTransformer("jinaai/jina-embeddings-v2-base-zh")
rag = RAGWithCitations("PleIAs/Pleias-RAG-1B")

# ---------------------
# 系統提示（依照設計需求）
# ---------------------
system_prompt = """
## 目標
分析廣告文字內容，根據法律條款和案例判斷廣告用詞是否涉及誇大療效及違法，並提供違法機率評估。回應內容必須完全依照格式，且使用繁體中文。回應簡潔有力，不需要提供分析過程的文字。

### 合規性判斷
- 無罪判定原則：不捏造或過度解讀廣告文字，從寬認定合法性，但如果是藥物宣稱科學實證、國外研究一類用語，則提高違法可能性認定，除非內容中出現完整的衛福部核可字號或衛福部認證。
- 比對允許使用的廣告用詞：
  - 「完整補充營養」「調整體質」「促進新陳代謝」「幫助入睡」「保護消化道全機能」「改變細菌叢生態」「排便有感」「在嚴謹的營養均衡與熱量控制，以及適當的運動條件下，適量攝取本產品有助於不易形成體脂肪」這些文字出現時不視為有違法風險。
  - 「能完整補充人體營養」、「調整體質」、「提升生理機能」、「調節生理機能」、「促進新陳代謝」、「幫助入睡」、「青春美麗」、「排便超有感」、「給你排便順暢新體驗」、「維持正常的排便習慣」、「排便順暢」、「改變細菌叢生態」、「保護消化道全機能」、「提升吸收滋養消化機能」這些文字出現時不視為有違法風險。

## 分析步驟
1. 解析廣告內容：檢視是否涉及療效誇大。
2. 文件檢索與法規比對：檢索 vector store 內的法律文件與案例，提供比對結果（文件 ID）。
3. 判斷違法機率：依據法律及案例進行風險評估。
4. 裁罰依據：
   - 《食品安全衛生管理法》第45條：違反第28條第1項：罰 4 萬至 400 萬元。

### 回應格式
只輸出一個字：T（違法）或 F（合法）
"""

# ---------------------
# 資料庫連線
# ---------------------
db = mysql.connector.connect(
    host="localhost",
    user="andyuser",
    password="adminpsw",
    database="ai_db"
)
cursor = db.cursor(dictionary=True)

# ---------------------
# 載入查詢 CSV
# ---------------------
query_df = pd.read_csv("the_query.csv")
results = []

# ---------------------
# 主迴圈：處理每一筆廣告語句
# ---------------------
for _, row in query_df.iterrows():
    query_id = row["ID"]
    query = row["Question"]

    # 查詢向量化
    q_vector = embedder.encode(query).astype("float32").tolist()

    # 從資料庫撈 embedding
    cursor.execute("""
        SELECT id, content, embedding FROM laws WHERE embedding IS NOT NULL
    """)
    laws = cursor.fetchall()

    def l2(v1, v2):
        return np.linalg.norm(np.array(v1) - np.array(v2))

    # 找前三筆相似法條
    top_laws = sorted(laws, key=lambda law: l2(q_vector, json.loads(law["embedding"])))[:3]
    sources = [{"text": law["content"], "metadata": {"source": f"law_id_{law['id']}"}} for law in top_laws]

    # 呼叫模型
    response = rag.generate(query=query, sources=sources, system_prompt=system_prompt)
    raw = response["processed"].get("clean_answer", "").strip().upper()

    # T=違法 -> Label=0；F=合法 -> Label=1
    if raw.startswith("T"):
        label = 0
    elif raw.startswith("F"):
        label = 1
    else:
        label = 1  # fallback 安全預設：視為合法

    results.append({"ID": query_id, "Label": label})

# ---------------------
# 輸出結果
# ---------------------
out_df = pd.DataFrame(results)
out_df.to_csv("tf_results.csv", index=False)
print("✅ 已輸出最終結果 tf_results.csv")
