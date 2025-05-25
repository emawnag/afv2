#!/usr/bin/env python3

import os
os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"

from pleias_rag_interface import RAGWithCitations

def main():
    try:
        print("初始化模型...")
        rag = RAGWithCitations("PleIAs/Pleias-RAG-1B")
        
        print("準備查詢...")
        query = "巴黎是哪裡?"
        sources = [
            {
                "text": "巴黎是法國的首都",
                "metadata": {"source": "Geographic Encyclopedia", "reliability": "high"}
            },
            {
                "text": "艾菲爾鐵塔在法國巴黎",
                "metadata": {"source": "Travel Guide", "year": 2020}
            }
        ]
        
        print("生成回應...")
        response = rag.generate(query, sources)
        
        print("處理完成！")
        print("回應:", response["processed"]["clean_answer"])
        
    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
