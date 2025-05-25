#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import mysql.connector
import pandas as pd
from typing import List, Dict, Any
import sys
import os
import re

# 添加 Pleias-RAG-Library 路徑
sys.path.append('/home/andy/aihw/f/Pleias-RAG-Library')
os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"

from pleias_rag_interface import RAGWithCitations

class DrugAdViolationRAG:
    def __init__(self, model_name="PleIAs/Pleias-RAG-1B"):
        """
        初始化藥物廣告違法判定RAG系統
        """
        print("初始化RAG模型...")
        self.rag_model = RAGWithCitations(model_name)
        
        print("連接資料庫...")
        self.db = mysql.connector.connect(
            host="localhost",
            user="andyuser", 
            password="adminpsw",
            database="ai_db"
        )
        self.cursor = self.db.cursor()
        
        # 系統提示詞
        self.system_prompt = """## 目標
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

請根據以上原則分析廣告內容，並給出最終判定結果：T（違法風險高）或F（風險低）。"""

    def translate_to_english(self, text: str) -> str:
        """
        簡單的中英文字詞映射翻譯（避免依賴外部翻譯服務）
        """
        # 簡單的關鍵詞映射表
        translation_dict = {
            # 藥物相關
            "藥物": "drug", "藥品": "medicine", "藥劑": "pharmaceutical",
            "療效": "therapeutic effect", "治療": "treatment", "醫療": "medical",
            "疾病": "disease", "病症": "illness", "症狀": "symptom",
            "健康": "health", "保健": "healthcare", "養生": "wellness",
            
            # 廣告用詞
            "廣告": "advertisement", "宣稱": "claim", "聲稱": "declare",
            "誇大": "exaggerate", "虛假": "false", "不實": "untrue",
            "療效": "efficacy", "效果": "effect", "功效": "effectiveness",
            
            # 法律相關
            "違法": "illegal", "合法": "legal", "法律": "law", "法規": "regulation",
            "條款": "clause", "條文": "article", "規定": "provision",
            "禁止": "prohibited", "允許": "permitted", "核准": "approved",
            
            # 常見詞彙
            "科學": "scientific", "研究": "research", "實證": "evidence",
            "證明": "prove", "顯示": "show", "表明": "indicate",
            "改善": "improve", "增強": "enhance", "提升": "boost",
            "營養": "nutrition", "補充": "supplement", "調整": "adjust",
            
            # 機構名稱
            "衛福部": "Ministry of Health and Welfare", "食藥署": "FDA Taiwan",
            "核可": "approval", "認證": "certification", "字號": "license number"
        }
        
        # 先進行關鍵詞替換
        translated_text = text
        for chinese, english in translation_dict.items():
            translated_text = translated_text.replace(chinese, english)
        
        # 如果還有中文字符，保持原文並添加英文標記
        if re.search(r'[\u4e00-\u9fff]', translated_text):
            return f"Chinese text analysis: {translated_text} (Original: {text})"
        
        return translated_text

    def get_law_sources_from_db(self, limit_sources=10) -> List[Dict[str, Any]]:
        """
        從資料庫獲取法規條文作為RAG的source，限制數量以避免超過模型長度限制
        """
        # 優先選擇藥事法和食品安全衛生管理法的重要條文
        query = """
        SELECT law_name, chapter, article_number, content 
        FROM laws 
        WHERE law_name IN ('食品安全衛生管理法', '藥事法') 
        AND (content LIKE '%廣告%' OR content LIKE '%宣傳%' OR content LIKE '%誇大%' OR content LIKE '%違法%' OR content LIKE '%禁止%')
        ORDER BY CASE 
            WHEN content LIKE '%廣告%' THEN 1
            WHEN content LIKE '%宣傳%' THEN 2  
            WHEN content LIKE '%誇大%' THEN 3
            ELSE 4
        END
        LIMIT %s
        """
        
        self.cursor.execute(query, (limit_sources,))
        results = self.cursor.fetchall()
        
        sources = []
        for row in results:
            law_name, chapter, article_number, content = row
            
            # 截短過長的法條內容
            if len(content) > 500:
                content = content[:500] + "..."
            
            # 翻譯法條內容到英文
            content_en = self.translate_to_english(content)
            
            source = {
                "text": content_en,
                "metadata": {
                    "law_name": law_name,
                    "chapter": chapter,
                    "article_number": article_number,
                    "original_text": content,
                    "source": "Taiwan Law Database",
                    "reliability": "high"
                }
            }
            sources.append(source)
            
        print(f"從資料庫獲取了 {len(sources)} 條相關法規條文")
        return sources

    def analyze_advertisement(self, ad_text: str) -> Dict[str, Any]:
        """
        分析單個廣告文字
        """
        # 截短過長的廣告文字
        if len(ad_text) > 1000:
            ad_text = ad_text[:1000] + "..."
        
        # 翻譯廣告文字到英文
        ad_text_en = self.translate_to_english(ad_text)
        
        # 建構更精確的查詢
        query_en = f"Analyze this advertisement for legal violations according to Taiwan drug and food safety laws: {ad_text_en}"
        
        # 獲取有限數量的相關法規條文作為sources
        sources = self.get_law_sources_from_db(limit_sources=8)
        
        # 使用RAG模型生成回應
        try:
            response = self.rag_model.generate(query_en, sources)
            return {
                "original_text": ad_text,
                "translated_text": ad_text_en,
                "rag_response": response,
                "sources_count": len(sources)
            }
        except Exception as e:
            print(f"RAG分析錯誤: {e}")
            return {
                "original_text": ad_text,
                "translated_text": ad_text_en,
                "error": str(e),
                "sources_count": len(sources)
            }

    def extract_violation_judgment(self, rag_response: Dict[str, Any], original_text: str) -> str:
        """
        從RAG回應中提取違法判定結果，並結合原始廣告文字進行關鍵詞分析
        """
        try:
            # 獲取RAG的回應文字
            if "processed" in rag_response and "clean_answer" in rag_response["processed"]:
                answer_text = rag_response["processed"]["clean_answer"].lower()
            else:
                answer_text = str(rag_response).lower()
            
            # 對原始廣告文字進行關鍵詞分析
            ad_text_lower = original_text.lower()
            
            # 高風險關鍵詞（違法可能性高）
            high_risk_keywords = [
                # 誇大療效用詞
                "治療", "治癒", "根治", "痊癒", "療效", "醫治",
                "cure", "treat", "heal", "therapeutic",
                # 科學實證相關（如果沒有衛福部字號）
                "科學實證", "臨床證實", "國外研究", "醫學證明",
                "scientific evidence", "clinical proven", "research shows",
                # 誇大用詞
                "神效", "奇效", "立即見效", "100%有效", "保證有效",
                "miracle", "instant effect", "100% effective", "guaranteed",
                # 疾病相關宣稱
                "減肥", "瘦身", "燃脂", "消脂", "排毒",
                "weight loss", "fat burning", "detox"
            ]
            
            # 中風險關鍵詞
            medium_risk_keywords = [
                "美白", "淡斑", "抗老", "緊緻", "除皺",
                "whitening", "anti-aging", "tightening"
            ]
            
            # 安全關鍵詞（合法用詞）
            safe_keywords = [
                "完整補充營養", "調整體質", "促進新陳代謝", "幫助入睡",
                "保護消化道全機能", "改變細菌叢生態", "排便有感",
                "提升生理機能", "調節生理機能", "青春美麗",
                "排便順暢", "維持正常的排便習慣",
                "提升吸收滋養消化機能"
            ]
            
            # 檢查是否有衛福部字號
            has_approval = any(keyword in ad_text_lower for keyword in [
                "衛福部", "衛生署", "核可字號", "許可證", "食字號", "健字號",
                "ministry approval", "health ministry", "license number"
            ])
            
            # 計算風險分數
            high_risk_score = sum(1 for keyword in high_risk_keywords if keyword in ad_text_lower)
            medium_risk_score = sum(1 for keyword in medium_risk_keywords if keyword in ad_text_lower)
            safe_score = sum(1 for keyword in safe_keywords if keyword in ad_text_lower)
            
            # RAG回應中的關鍵詞分析
            rag_violation_keywords = [
                "illegal", "violation", "prohibited", "unlawful", "violates",
                "false claim", "misleading", "exaggerated", "not permitted"
            ]
            rag_safe_keywords = [
                "legal", "compliant", "acceptable", "permitted", "allowed",
                "no violation", "within regulations", "complies"
            ]
            
            rag_violation_score = sum(1 for keyword in rag_violation_keywords if keyword in answer_text)
            rag_safe_score = sum(1 for keyword in rag_safe_keywords if keyword in answer_text)
            
            # 判定邏輯
            total_risk_score = high_risk_score * 3 + medium_risk_score * 1.5 + rag_violation_score * 2
            total_safe_score = safe_score * 2 + rag_safe_score * 1.5
            
            # 如果有衛福部字號，降低風險分數
            if has_approval:
                total_risk_score *= 0.5
            
            # 最終判定
            if total_risk_score > total_safe_score and total_risk_score > 2:
                return "T"  # 違法風險高
            else:
                return "F"  # 風險低
                
        except Exception as e:
            print(f"判定提取錯誤: {e}")
            return "F"  # 預設為風險低

    def process_queries_from_csv(self, input_csv_path: str, output_csv_path: str):
        """
        處理CSV檔案中的查詢並輸出結果
        """
        print(f"讀取查詢檔案: {input_csv_path}")
        
        # 讀取查詢檔案
        queries_df = pd.read_csv(input_csv_path)
        
        results = []
        
        for index, row in queries_df.iterrows():
            query_id = row['ID']
            question = row['Question']
            
            print(f"處理查詢 {query_id}: {question[:100]}...")
            
            # 分析廣告
            analysis_result = self.analyze_advertisement(question)
            
            # 提取違法判定
            if "rag_response" in analysis_result:
                judgment = self.extract_violation_judgment(analysis_result["rag_response"], question)
            else:
                judgment = "F"  # 如果分析失敗，預設為風險低
            
            # 轉換判定結果為數字 (T=1, F=0)
            judgment_numeric = 1 if judgment == "T" else 0
            
            results.append({
                "ID": query_id,
                "Answer": judgment_numeric
            })
            
            print(f"查詢 {query_id} 完成，判定: {judgment} ({judgment_numeric})")
        
        # 保存結果
        results_df = pd.DataFrame(results)
        results_df.to_csv(output_csv_path, index=False)
        print(f"結果已保存到: {output_csv_path}")
        
        return results

    def __del__(self):
        """
        清理資源
        """
        if hasattr(self, 'cursor'):
            self.cursor.close()
        if hasattr(self, 'db'):
            self.db.close()

def main():
    """
    主程式
    """
    try:
        # 初始化RAG系統
        rag_system = DrugAdViolationRAG()
        
        # 處理查詢檔案
        input_csv = "/home/andy/aihw/f/the_query.csv"
        output_csv = "/home/andy/aihw/f/drug_ad_violation_results.csv"
        
        # 執行分析
        results = rag_system.process_queries_from_csv(input_csv, output_csv)
        
        print("=== 處理完成 ===")
        print(f"總共處理了 {len(results)} 個查詢")
        
        # 統計結果
        violation_count = sum(1 for r in results if r["Answer"] == 1)
        safe_count = len(results) - violation_count
        
        print(f"違法風險高: {violation_count} 個")
        print(f"風險低: {safe_count} 個")
        
    except Exception as e:
        print(f"主程式錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
