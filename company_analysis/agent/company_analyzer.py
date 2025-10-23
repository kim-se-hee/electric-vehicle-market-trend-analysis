"""
Company Analyzer Agent
RAG를 활용한 기업 분석 에이전트
"""
from typing import Dict, Any, List
from common.agent.base_agent import BaseAgent
from company_analysis.tools.rag_tool import RAGTool
from company_analysis.tools.document_loader import DocumentLoader
from langchain_core.messages import HumanMessage, AIMessage


class CompanyAnalyzerAgent(BaseAgent):
    """기업 분석 에이전트 - RAG 기반"""
    
    def __init__(self):
        super().__init__(name="CompanyAnalyzer")
        self.doc_loader = DocumentLoader()
        self.rag_tool = RAGTool()
        
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        기업 분석 실행
        
        Args:
            state: 현재 상태 (market_research에서 기업 리스트 및 문서 가져옴)
            
        Returns:
            업데이트된 상태
        """
        try:
            self.log_start()
            
            # 분석할 기업 리스트 가져오기
            companies = self._get_target_companies(state)
            self.logger.info(f"📋 분석 대상 기업: {', '.join(companies)}")
            
            # State에서 문서 가져오기 시도
            documents = self._get_documents_from_state(state)
            
            if not documents:
                # State에 문서가 없으면 직접 수집
                self.logger.info("\n📥 State에 문서 없음. 기업 문서 수집 중...")
                documents = self.doc_loader.load_company_documents(companies)
                self.logger.info(f"✅ 총 {len(documents)}개 문서 수집 완료")
            else:
                self.logger.info(f"✅ State에서 {len(documents)}개 문서 가져옴")
            
            self.logger.info(f"🔧 벡터 DB 구축 중...")
            self.rag_tool.build_vectorstore(documents)
            
            # 각 기업 분석
            company_analyses = {}
            for company in companies:
                self.logger.info(f"\n🔍 {company} 분석 중...")
                analysis = self._analyze_company(company)
                company_analyses[company] = analysis
                self.logger.info(f"✅ {company} 분석 완료")
            
            # State 업데이트
            state["company_analysis"] = company_analyses
            state["company_analysis_done"] = True
            
            # 메시지 추가
            summary = self._create_summary(company_analyses)
            if "messages" not in state:
                state["messages"] = []
            state["messages"].append(
                AIMessage(content=f"기업 분석 완료:\n{summary}")
            )
            
            self.log_complete()
            return state
            
        except Exception as e:
            return self.handle_error(e, state)
    
    def _get_target_companies(self, state: Dict[str, Any]) -> List[str]:
        """
        분석 대상 기업 리스트 추출
        
        우선순위:
        1. State의 companies 필드 (Market Researcher가 저장한 것)
        2. market_research의 key_companies
        3. 기본 기업 리스트
        """
        # 1순위: State에 직접 저장된 companies
        companies_from_state = state.get("companies", [])
        if companies_from_state:
            self.logger.info(f"✅ State에서 기업 리스트 발견: {companies_from_state}")
            return companies_from_state[:5]  # 최대 5개
        
        # 2순위: market_research 안의 key_companies
        market_research = state.get("market_research", {})
        key_companies = market_research.get("key_companies", [])
        if key_companies:
            self.logger.info(f"✅ market_research에서 기업 리스트 발견: {key_companies}")
            return key_companies[:5]
        
        # 3순위: 기본 리스트
        self.logger.warning("⚠️ State에 기업 리스트 없음. 기본 리스트 사용")
        default_companies = [
            "Tesla",
            "BYD", 
            "Samsung SDI",
            "LG Energy Solution",
            "CATL"
        ]
        return default_companies
    
    def _get_documents_from_state(self, state: Dict[str, Any]) -> List:
        """
        State에서 문서 가져오기
        
        Market Researcher가 수집한 문서를 재사용
        """
        from langchain.schema import Document
        
        documents = []
        
        # 1. market_research의 summary를 Document로 변환
        market_research = state.get("market_research", {})
        if market_research:
            summary = market_research.get("summary", "")
            if summary:
                doc = Document(
                    page_content=summary,
                    metadata={
                        "source": "market_research_summary",
                        "type": "market_overview"
                    }
                )
                documents.append(doc)
            
            # key_trends도 텍스트로 변환
            key_trends = market_research.get("key_trends", [])
            if key_trends:
                trends_text = "\n\n".join([
                    f"트렌드: {t.get('title', '')}\n설명: {t.get('description', '')}"
                    for t in key_trends
                ])
                doc = Document(
                    page_content=trends_text,
                    metadata={
                        "source": "market_research_trends",
                        "type": "trends"
                    }
                )
                documents.append(doc)
        
        # 2. references (URL 리스트)는 현재 content가 없으므로 스킵
        # 나중에 DocumentLoader에서 다시 가져옴
        
        return documents
    
    def _analyze_company(self, company: str) -> Dict[str, Any]:
        """
        개별 기업 상세 분석
        
        Args:
            company: 기업명
            
        Returns:
            기업 분석 결과
        """
        # RAG를 통한 질의응답
        questions = [
            f"{company}의 2024-2025년 주요 사업 전략은?",
            f"{company}의 핵심 제품 라인업은?",
            f"{company}의 주요 파트너십과 협력 관계는?",
            f"{company}의 기술적 강점과 차별화 요소는?",
            f"{company}가 직면한 주요 리스크와 도전과제는?"
        ]
        
        answers = {}
        for question in questions:
            answer = self.rag_tool.query(question)
            # 질문을 키로 변환 (간단하게)
            key = question.split("?")[0].split("는")[-1].split("은")[-1].strip()
            answers[key] = answer
        
        # LLM으로 종합 분석
        analysis_prompt = f"""
다음은 {company}에 대해 수집한 정보입니다:

{self._format_answers(answers)}

위 정보를 바탕으로 {company}의 현황을 다음 항목으로 요약해주세요:

1. 회사 개요 (2-3문장)
2. 핵심 강점 (3-5개 bullet points)
3. 주요 약점/리스크 (3-5개 bullet points)
4. 2025년 전망 (2-3문장)

각 항목을 명확하게 구분하여 작성해주세요.
"""
        
        response = self.llm.invoke(analysis_prompt)
        
        return {
            "company_name": company,
            "detailed_qa": answers,
            "summary_analysis": response.content,
            "last_updated": "2025-10-23"
        }
    
    def _format_answers(self, answers: Dict[str, str]) -> str:
        """답변을 포맷팅"""
        formatted = []
        for key, answer in answers.items():
            formatted.append(f"**{key}**\n{answer}\n")
        return "\n".join(formatted)
    
    def _create_summary(self, analyses: Dict[str, Any]) -> str:
        """전체 기업 분석 요약"""
        summary_parts = []
        for company, analysis in analyses.items():
            summary_parts.append(f"• {company}: 분석 완료")
        return "\n".join(summary_parts)