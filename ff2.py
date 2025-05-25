from transformers import pipeline
import pandas as pd
import mysql.connector
import numpy as np
from sentence_transformers import SentenceTransformer
import json

# ---------------------
# 初始化模型
# ---------------------
embedder = SentenceTransformer("jinaai/jina-embeddings-v2-base-zh")
generator = pipeline("text-generation", model="PleIAs/Pleias-RAG-1B")

# ---------------------
# 系統提示
# ---------------------
system_prompt = """## 目標
分析廣告文字內容，根據法律條款和案例判斷廣告用詞是否涉及誇大療效及違法，並提供違法機率評估。回應內容必須完全依照格式，且使用繁體中文。回應簡潔有力，不需要提供分析過程的文字。

### 合規性判斷
- **無罪判定原則**：不捏造或過度解讀廣告文字，**從寬認定合法性**，但如果是**藥物**宣稱**科學實證**、**國外研究**一類用語，則提高違法可能性認定，除非內容中出現完整的**衛福部核可字號**或**衛福部認證**。
- **比對允許使用的廣告用詞**：
  - 「完整補充營養」「調整體質」「促進新陳代謝」「幫助入睡」「保護消化道全機能」「改變細菌叢生態」「排便有感」「在嚴謹的營養均衡與熱量控制，以及適當的運動條件下，適量攝取本產品有助於不易形成體脂肪」這些文字出現時不視為有違法風險。
 - 「能完整補充人體營養」、「調整體質」、「提升生理機能」、「調節生理機能」、「促進新陳代謝」、「幫助入睡」、「調整體質」、「青春美麗」、「排便超有感」、「給你排便順暢新體驗」、「維持正常的排便習慣」、「排便順暢」、「促進新陳代謝」、「調整體質」、「改變細菌叢生態」、調節生理機能」、「保護消化道全機能」、「提升吸收滋養消化機能」"這些文字出現時不視為有違法風險。

## 分析步驟
1. **解析廣告內容**：檢視是否涉及療效誇大。
2. **文件檢索與法規比對**：檢索 `vector store` 內的法律文件與案例，提供比對結果（文件 ID）。
3. **判斷違法機率**：依據法律及案例進行風險評估。
4. **裁罰依據**：
   法規名稱-條文-罰款
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
# 主迴圈
# ---------------------
for i, row in query_df.iterrows():
    query = row["Question"]

    q_vector = embedder.encode(query).astype("float32").tolist()

    cursor.execute("SELECT id, content, embedding FROM laws WHERE embedding IS NOT NULL")
    laws = cursor.fetchall()

    def l2(v1, v2):
        return np.linalg.norm(np.array(v1) - np.array(v2))

    top_laws = sorted(laws, key=lambda law: l2(q_vector, json.loads(law["embedding"])))[:3]
    context_text = "\n\n".join([law["content"] for law in top_laws])

    # 組合 prompt
    prompt = f"{system_prompt}\n\n【廣告語句】{query}\n\n【相關法條】\n{context_text}\n\n請輸出 T 或 F："

    # 呼叫模型
    response = generator(prompt, max_new_tokens=10, do_sample=False)[0]["generated_text"]
    raw = response.strip().split(prompt)[-1].strip().upper()

    if raw.startswith("T"):
        label = 0
    elif raw.startswith("F"):
        label = 1
    else:
        label = 1  # fallback

    results.append({"ID": i, "Label": label})

# ---------------------
# 輸出結果
# ---------------------
out_df = pd.DataFrame(results)
out_df.to_csv("tf_results.csv", index=False)
print("✅ 已輸出最終結果 tf_results.csv")
