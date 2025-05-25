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

# 檢查欄位是否存在
cursor.execute("""
    SELECT COUNT(*) AS cnt
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE table_schema = 'ai_db'
      AND table_name = 'laws'
      AND column_name = 'embedding'
""")
if cursor.fetchone()["cnt"] == 0:
    print("🔧 欄位 'embedding' 不存在，建立中...")
    cursor.execute("ALTER TABLE laws ADD COLUMN embedding JSON")
    print("✅ 欄位已建立")
else:
    print("ℹ️ 欄位 'embedding' 已存在，略過建立")

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
