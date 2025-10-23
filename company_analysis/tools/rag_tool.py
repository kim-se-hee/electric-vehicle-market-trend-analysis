"""
RAG Tool
벡터 DB 기반 검색 증강 생성
"""
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain.schema import Document
from config.settings import settings
import logging


class RAGTool:
    """RAG 시스템"""
    
    def __init__(self):
        self.logger = logging.getLogger("RAGTool")
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY
        )
        self.vectorstore: Optional[FAISS] = None
        self.qa_chain: Optional[RetrievalQA] = None
        
    def build_vectorstore(self, documents: List[Document]) -> None:
        """
        문서로부터 벡터 DB 구축
        
        Args:
            documents: Document 리스트
        """
        if not documents:
            self.logger.warning("⚠️  문서가 없어 벡터 DB를 구축할 수 없습니다")
            return
        
        self.logger.info(f"🔧 {len(documents)}개 문서로 벡터 DB 구축 중...")
        
        # FAISS 벡터스토어 생성
        self.vectorstore = FAISS.from_documents(
            documents=documents,
            embedding=self.embeddings
        )
        
        # QA 체인 생성
        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 5}  # 상위 5개 문서 검색
            ),
            return_source_documents=True
        )
        
        self.logger.info("✅ 벡터 DB 구축 완료")
    
    def query(self, question: str) -> str:
        """
        RAG 질의
        
        Args:
            question: 질문
            
        Returns:
            답변
        """
        if not self.qa_chain:
            return "벡터 DB가 구축되지 않았습니다."
        
        try:
            result = self.qa_chain.invoke({"query": question})
            return result["result"]
            
        except Exception as e:
            self.logger.error(f"❌ RAG 질의 실패: {e}")
            return f"질의 처리 중 오류 발생: {str(e)}"
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """
        유사도 검색
        
        Args:
            query: 검색 쿼리
            k: 반환할 문서 개수
            
        Returns:
            관련 문서 리스트
        """
        if not self.vectorstore:
            return []
        
        return self.vectorstore.similarity_search(query, k=k)
    
    def save_vectorstore(self, path: str) -> None:
        """벡터스토어 저장"""
        if self.vectorstore:
            self.vectorstore.save_local(path)
            self.logger.info(f"💾 벡터 DB 저장: {path}")
    
    def load_vectorstore(self, path: str) -> None:
        """벡터스토어 로드"""
        try:
            self.vectorstore = FAISS.load_local(
                path, 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            
            # QA 체인 재생성
            llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                temperature=0.0,
                api_key=settings.OPENAI_API_KEY
            )
            
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(
                    search_kwargs={"k": 5}
                ),
                return_source_documents=True
            )
            
            self.logger.info(f"📂 벡터 DB 로드 완료: {path}")
            
        except Exception as e:
            self.logger.error(f"❌ 벡터 DB 로드 실패: {e}")