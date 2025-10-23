"""
Market Researcher Agent
전기차 시장 트렌드와 산업 현황을 조사하는 에이전트
"""

from common.agent.base_agent import BaseAgent
from market_research.tool.tools import (
    TavilySearchTool,
    WebContentFetcher,
    filter_reliable_sources,
    deduplicate_results
)
from market_research.prompt.prompts import (
    MARKET_ANALYSIS_SYSTEM_PROMPT,
    SEARCH_QUERY_GENERATION_PROMPT,
    MARKET_SYNTHESIS_PROMPT
)
from market_research.schema.schemas import MarketResearchOutput
from market_research.utils import (
    extract_json_from_text,
    truncate_documents,
    merge_search_results
)
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Dict
import asyncio

class MarketResearcherAgent(BaseAgent):
    """시장 조사 에이전트"""
    
    def __init__(self):
        super().__init__(name="Market_Researcher")
        self.searcher = TavilySearchTool(max_results=5)
        self.fetcher = WebContentFetcher()
    
    def run(self, state):
        """에이전트 실행"""
        self.log_start()
        
        try:
            # 1. 사용자 요청 파악
            user_request = state.get("user_request", "전기차 시장 분석")
            self.logger.info(f"사용자 요청: {user_request}")
            
            # 2. 검색 쿼리 생성
            search_queries = self._generate_search_queries(user_request)
            self.logger.info(f"생성된 검색 쿼리: {search_queries}")
            
            # 3. 웹 검색 실행
            all_search_results = self._execute_searches(search_queries)
            self.logger.info(f"총 {len(all_search_results)}개 검색 결과 수집")
            
            # 4. 신뢰도 높은 소스 필터링
            filtered_results = filter_reliable_sources(all_search_results)
            filtered_results = deduplicate_results(filtered_results)
            self.logger.info(f"필터링 후 {len(filtered_results)}개 결과")
            
            # 5. 상세 문서 가져오기 (상위 5-10개)
            top_results = filtered_results[:10]
            urls = [r['url'] for r in top_results]
            documents = asyncio.run(self.fetcher.fetch_multiple(urls))
            self.logger.info(f"{len(documents)}개 상세 문서 로딩 완료")
            
            # 6. 문서를 토큰 제한에 맞게 자르기
            documents = truncate_documents(documents, max_tokens=8000)
            
            # 7. LLM으로 종합 분석
            analysis_result = self._analyze_with_llm(documents, top_results)
            
            # 8. 구조화된 출력 생성
            output = self._create_output(analysis_result, top_results)
            
            self.log_complete()
            
            return {
                "market_research": output.dict(),
                "companies": output.key_companies,  # ← 추가됨!
                "references": output.sources,
                "messages": [HumanMessage(
                    content=f"시장 조사를 완료했습니다. "
                            f"{len(output.key_companies)}개 주요 기업, "
                            f"{len(output.key_trends)}개 주요 트렌드, "
                            f"{len(output.risks)}개 리스크 요인을 발견했습니다.",
                    name=self.name
                )]
            }
            
        except Exception as e:
            self.logger.error(f"에이전트 실행 실패: {e}", exc_info=True)
            return self.handle_error(e, state)
    
    def _generate_search_queries(self, user_request: str) -> List[str]:
        """검색 쿼리 생성"""
        # LLM을 사용하여 동적 쿼리 생성도 가능하지만,
        # 여기서는 고정된 효과적인 쿼리 사용
        queries = [
            "electric vehicle market trends 2025",
            "EV sales growth forecast 2025",
            "전기차 시장 전망 2025",
            "lithium battery supply chain issues 2025",
            "EV market outlook Asia Pacific",
            "전기차 배터리 공급망",
            "Tesla BYD market share 2025",
            "electric vehicle industry challenges"
        ]
        
        # 사용자 요청에서 특정 키워드 추출하여 추가 가능
        if "Tesla" in user_request or "테슬라" in user_request:
            queries.append("Tesla market strategy 2025")
        if "BYD" in user_request:
            queries.append("BYD electric vehicle growth")
        
        return queries
    
    def _execute_searches(self, queries: List[str]) -> List[Dict]:
        """여러 쿼리로 검색 실행"""
        all_results = []
        
        for query in queries:
            self.logger.info(f"검색 중: {query}")
            results = self.searcher.search_web(query)
            all_results.extend(results)
        
        # 중복 제거 및 병합
        return deduplicate_results(all_results)
    
    def _analyze_with_llm(self, documents: List[str], search_results: List[Dict]) -> dict:
        """LLM으로 문서 분석"""
        # 문서와 출처 준비
        docs_text = "\n\n---\n\n".join([
            f"[문서 {i+1}]\n{doc[:3000]}"  # 각 문서 최대 3000자
            for i, doc in enumerate(documents)
        ])
        
        sources_text = "\n".join([
            f"[문서 {i+1}] {result['title']} - {result['url']}"
            for i, result in enumerate(search_results[:len(documents)])
        ])
        
        # 프롬프트 구성
        prompt = MARKET_SYNTHESIS_PROMPT.format(
            documents=docs_text,
            sources=sources_text
        )
        
        messages = [
            SystemMessage(content=MARKET_ANALYSIS_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        # LLM 호출
        self.logger.info("LLM 분석 시작...")
        response = self.llm.invoke(messages)
        
        # JSON 추출
        analysis = extract_json_from_text(response.content)
        
        if not analysis:
            self.logger.warning("JSON 파싱 실패, 응답 원문 사용")
            # 파싱 실패 시 기본 구조 반환
            analysis = {
                "summary": response.content[:500],
                "market_size": "N/A",
                "growth_rate": "N/A",
                "key_companies": [],
                "key_trends": [],
                "opportunities": [],
                "risks": [],
                "battery_supply_chain": "정보 부족"
            }
        
        return analysis
    
    def _create_output(self, analysis: dict, search_results: List[Dict]) -> MarketResearchOutput:
        """구조화된 출력 생성"""
        # 출처 URL 추출
        sources = [r['url'] for r in search_results[:10]]
        
        # MarketResearchOutput 객체 생성
        output = MarketResearchOutput(
            summary=analysis.get('summary', ''),
            market_size=analysis.get('market_size'),
            growth_rate=analysis.get('growth_rate', 'N/A'),
            key_companies=analysis.get('key_companies', []),  # ← 추가됨!
            key_trends=analysis.get('key_trends', []),
            opportunities=analysis.get('opportunities', []),
            risks=analysis.get('risks', []),
            battery_supply_chain=analysis.get('battery_supply_chain'),
            sources=sources
        )
        
        return output