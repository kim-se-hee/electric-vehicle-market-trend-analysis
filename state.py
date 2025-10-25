"""
Multi-Agent System State Definition
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
import operator

class AgentState(TypedDict):
    """멀티 에이전트 시스템의 공유 상태"""
    
    # 입력
    user_request: str  # 사용자 요청
    
    # Market Researcher 출력
    market_research: Optional[Dict[str, Any]]  # 시장 조사 결과
    companies: Annotated[List[str], operator.add]  # 발견된 주요 기업 리스트
    references: Annotated[List[str], operator.add]  # 참고 자료 URL
    
    # Company Analyzer 출력
    company_analysis: Optional[Dict[str, Any]]  # 기업 분석 결과
    
    # Stock Analyzer 출력 
    stock_analysis: Optional[Dict[str, Any]]  # 주가/재무 분석 결과
    ticker_symbols: Annotated[List[str], operator.add]  # 분석된 티커 리스트
    stock_data: Optional[Dict[str, Dict]]  # {ticker: raw_data} 원본 주식 데이터
    
    # 에이전트 간 통신
    messages: Annotated[List, operator.add]  # 에이전트 메시지 로그