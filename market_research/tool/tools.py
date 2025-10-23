from typing import List, Dict, Optional
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain.tools import tool
from common.config.settings import settings  # .env에서 가져온 settings 사용
import asyncio
import aiohttp
import os

os.environ["TAVILY_API_KEY"] = settings.TAVILY_API_KEY  # ← 추가
os.environ["USER_AGENT"] = "MyEVMarketAnalysisBot/1.0"  # ← 추가

class TavilySearchTool:
    """Tavily 검색 도구 래퍼"""
    
    def __init__(self, max_results: int = 5):
        self.search = TavilySearchResults(
            max_results=max_results,
            search_depth="advanced",  # "basic" 또는 "advanced"
            include_answer=True,
            include_raw_content=True,
            include_images=False,
            api_key=settings.TAVILY_API_KEY  # ✅ .env에서 가져옴
        )
    
    def search_web(self, query: str) -> List[Dict]:
        """웹 검색 실행"""
        try:
            results = self.search.invoke({"query": query})
            
            # Tavily 결과 포맷 정리
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0),
                    "raw_content": result.get("raw_content", "")
                })
            
            return formatted_results
        except Exception as e:
            print(f"검색 실패: {query}, 에러: {e}")
            return []


class WebContentFetcher:
    """웹 페이지 전체 내용 가져오기"""
    
    @staticmethod
    async def fetch_single_url(session, url: str, timeout: int = 10) -> tuple[str, str]:
        """단일 URL 비동기 다운로드"""
        try:
            print(f"  → {url[:60]}...")
            async with session.get(url, timeout=timeout, ssl=False) as response:
                html = await response.text()
                print(f"    ✅ 성공 ({len(html)}자)")
                return url, html
        except asyncio.TimeoutError:
            print(f"    ⏰ 타임아웃 (10초 초과)")
            return url, ""
        except Exception as e:
            print(f"    ❌ 실패: {type(e).__name__}")
            return url, ""
    
    @staticmethod
    async def fetch_multiple(urls: List[str], timeout: int = 10) -> List[str]:
        """여러 URL의 내용을 비동기로 가져오기"""
        print(f"\n📥 {len(urls)}개 URL 문서 로딩 시작...")
        
        try:
            # aiohttp로 직접 다운로드 (더 빠르고 안정적)
            async with aiohttp.ClientSession() as session:
                tasks = [WebContentFetcher.fetch_single_url(session, url, timeout) for url in urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # HTML을 텍스트로 변환
            print("\n📝 HTML → 텍스트 변환 중...")
            documents = []
            for url, html in results:
                if html and not isinstance(html, Exception):
                    # 간단한 HTML → 텍스트 변환
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    # 스크립트와 스타일 제거
                    for script in soup(["script", "style"]):
                        script.decompose()
                    text = soup.get_text()
                    # 공백 정리
                    lines = (line.strip() for line in text.splitlines())
                    text = '\n'.join(line for line in lines if line)
                    documents.append(text)
            
            print(f"✅ {len(documents)}개 문서 로딩 완료\n")
            return documents
            
        except Exception as e:
            print(f"❌ 문서 로딩 실패: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def fetch_single(url: str) -> str:
        """단일 URL 동기 방식"""
        print(f"📄 단일 URL 로딩: {url[:50]}...")
        try:
            result = asyncio.run(WebContentFetcher.fetch_multiple([url]))
            return result[0] if result else ""
        except Exception as e:
            print(f"❌ 문서 로딩 실패: {url}, {e}")
            return ""



def filter_reliable_sources(results: List[Dict]) -> List[Dict]:
    """신뢰도 높은 소스만 필터링"""
    # 신뢰도 높은 도메인 리스트
    reliable_domains = [
        'bloomberg.com',
        'reuters.com',
        'ft.com',
        'wsj.com',
        'iea.org',
        'mckinsey.com',
        'bcg.com',
        'deloitte.com',
        'pwc.com',
        'tesla.com',
        'marketwatch.com',
        'cnbc.com',
        'insideevs.com',
        'electrek.co',
        'cleantechnica.com'
    ]
    
    # 한국 신뢰 소스
    korean_domains = [
        'mk.co.kr',
        'hankyung.com',
        'chosun.com',
        'joongang.co.kr',
        'etnews.com'
    ]
    
    all_reliable = reliable_domains + korean_domains
    
    filtered = []
    for result in results:
        url = result.get('url', '').lower()
        if any(domain in url for domain in all_reliable):
            filtered.append(result)
    
    # 신뢰 소스가 없으면 점수 높은 순으로 반환
    if not filtered:
        return sorted(results, key=lambda x: x.get('score', 0), reverse=True)[:5]
    
    return filtered


def deduplicate_results(results: List[Dict]) -> List[Dict]:
    """중복 URL 제거"""
    seen_urls = set()
    unique = []
    
    for result in results:
        url = result.get('url')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(result)
    
    return unique


@tool
def search_ev_market(query: str) -> str:
    """
    전기차 시장 관련 정보를 웹에서 검색합니다.
    
    Args:
        query: 검색 쿼리
    
    Returns:
        검색 결과 요약
    """
    searcher = TavilySearchTool(max_results=settings.TAVILY_MAX_RESULTS)  # ✅ settings 사용
    results = searcher.search_web(query)
    
    if not results:
        return "검색 결과를 찾을 수 없습니다."
    
    # 결과 요약
    summary = f"'{query}' 검색 결과 {len(results)}건:\n\n"
    for i, result in enumerate(results, 1):
        summary += f"{i}. {result['title']}\n"
        summary += f"   {result['content'][:200]}...\n"
        summary += f"   출처: {result['url']}\n\n"
    
    return summary