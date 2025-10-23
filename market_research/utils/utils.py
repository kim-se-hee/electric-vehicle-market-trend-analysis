from typing import List, Dict
import json
import re

def extract_json_from_text(text: str) -> dict:
    """LLM 응답에서 JSON 추출"""
    try:
        # 응답에서 json 코드 블록 정규식 기반 매칭
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # 응답에서 일반 json 정규식 기반 매칭
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        
        return {}
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 실패: {e}")
        return {}


def truncate_documents(documents: List[str], max_tokens: int = 8000) -> List[str]:
    """문서를 토큰 제한에 맞게 자르기"""
    truncated = []
    total_chars = 0
    # 대략 1 토큰 = 4 글자로 계산
    max_chars = max_tokens * 4
    
    for doc in documents:
        if total_chars + len(doc) <= max_chars:
            truncated.append(doc)
            total_chars += len(doc)
        else:
            remaining = max_chars - total_chars
            if remaining > 500:  # 최소 500자는 포함
                truncated.append(doc[:remaining])
            break
    
    return truncated


def calculate_relevance_score(result: Dict, keywords: List[str]) -> float:
    """검색 결과의 관련성 점수 계산"""
    content = (result.get('title', '') + ' ' + result.get('content', '')).lower()
    
    score = 0.0
    for keyword in keywords:
        if keyword.lower() in content:
            score += 1.0
    
    # Tavily 자체 점수도 반영
    tavily_score = result.get('score', 0)
    
    return (score + tavily_score) / 2


def merge_search_results(results_list: List[List[Dict]]) -> List[Dict]:
    """여러 검색 결과를 병합하고 중복 제거"""
    all_results = []
    seen_urls = set()
    
    for results in results_list:
        for result in results:
            url = result.get('url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append(result)
    
    # 점수 순으로 정렬
    all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    return all_results