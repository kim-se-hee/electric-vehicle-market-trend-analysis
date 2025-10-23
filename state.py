"""
Multi-Agent System State Definition
"""

from typing import TypedDict, Annotated, List, Dict, Any
import operator

class AgentState(TypedDict):
    """멀티 에이전트 시스템의 공유 상태"""
    
    # 입력
    user_request: str  # 사용자 요청
    
    # Market Researcher 출력
    market_research: Dict[str, Any]  # 시장 조사 결과
    companies: Annotated[List[str], operator.add]  # 발견된 주요 기업 리스트
    references: Annotated[List[str], operator.add]  # 참고 자료 URL
    
    # Company Analyzer 출력
    company_analysis: Dict[str, Any]  # 기업 분석 결과
    
    # 에이전트 간 통신
    messages: Annotated[List, operator.add]  # 에이전트 메시지 로그