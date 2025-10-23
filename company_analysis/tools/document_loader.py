"""
Document Loader
기업 문서 수집 도구
"""
from typing import List
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from common.config.settings import settings
import logging
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

class DocumentLoader:
    """기업 관련 문서 수집"""
    
    def __init__(self):
        self.logger = logging.getLogger("DocumentLoader")
        self.search_tool = TavilySearchResults(
            max_results=settings.TAVILY_MAX_RESULTS,
            api_key=settings.TAVILY_API_KEY
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def load_company_documents(self, companies: List[str]) -> List[Document]:
        """
        기업들의 문서 수집
        
        Args:
            companies: 기업명 리스트
            
        Returns:
            Document 리스트
        """
        all_documents = []
        
        for company in companies:
            self.logger.info(f"📄 {company} 문서 수집 중...")
            docs = self._load_single_company(company)
            all_documents.extend(docs)
            self.logger.info(f"  → {len(docs)}개 문서 수집")
        
        return all_documents
    
    def _load_single_company(self, company: str) -> List[Document]:
        """단일 기업 문서 수집"""
        documents = []
        
        # 1. 웹 검색으로 관련 URL 찾기
        search_queries = [
            f"{company} 전기차 사업 전략 2025",
            f"{company} 배터리 기술 제품",
            f"{company} IR 자료 실적",
            f"{company} 파트너십 협력"
        ]
        
        urls = set()
        for query in search_queries:
            try:
                results = self.search_tool.invoke({"query": query})
                for result in results:
                    if isinstance(result, dict) and "url" in result:
                        urls.add(result["url"])
            except Exception as e:
                self.logger.warning(f"검색 실패 ({query}): {e}")
        
        # 2. URL에서 문서 로드
        for url in list(urls)[:10]:  # 최대 10개 URL
            try:
                loader = WebBaseLoader(url)
                docs = loader.load()
                
                # 메타데이터 추가
                for doc in docs:
                    doc.metadata["company"] = company
                    doc.metadata["source_url"] = url
                
                documents.extend(docs)
                
            except Exception as e:
                self.logger.warning(f"문서 로드 실패 ({url}): {e}")
        
        # 3. 문서 분할
        if documents:
            split_documents = self.text_splitter.split_documents(documents)
            return split_documents
        
        return []