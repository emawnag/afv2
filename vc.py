from sentence_transformers import SentenceTransformer
import mysql.connector
import numpy as np
import json

# 初始化向量模型
model = SentenceTransformer("jinaai/jina-embeddings-v2-base-zh")

# 連接 MySQL
db = mysql.connector.connect(
    host="localhost",
    user="andyuser",
    password="adminpsw",
    database="ai_db"
)
cursor = db.cursor(dictionary=True)

# 建立向量儲存欄位（如尚未建立）
cursor.execute("""
ALTER TABLE laws ADD COLUMN IF NOT EXISTS embedding JSON
""")

# 擷取所有條文
cursor.execute("SELECT id, content FROM laws")
rows = cursor.fetchall()

# 向量化並更新到資料庫
for row in rows:
    embedding = model.encode(row["content"]).tolist()
    sql = "UPDATE laws SET embedding = %s WHERE id = %s"
    cursor.execute(sql, (json.dumps(embedding), row["id"]))

db.commit()
print("✅ 條文向量已全部更新到資料庫")

cursor.close()
db.close()
