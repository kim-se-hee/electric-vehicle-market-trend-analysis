"""
Stock Analyzer Agent
FinanceDataReader를 활용한 주식/재무 분석 에이전트
"""
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from stock_analysis.tools.finance_data_reader import FDRTool
from stock_analysis.schemas.stock_schema import StockAnalysisResult
from stock_analysis.prompts.stock_prompts import STOCK_ANALYSIS_PROMPT


class StockAnalyzerAgent:
    """
    주식 및 재무 분석 에이전트
    
    특징:
    - FinanceDataReader 사용 (Rate Limit 없음)
    - 한국/미국 주식 지원
    - 가격 정보, 거래량, 추세 분석
    - 재무 지표 분석
    """
    
    def __init__(
        self,
        llm: ChatOpenAI,
        logger: Optional[logging.Logger] = None
    ):
        """
        Args:
            llm: LangChain LLM 인스턴스
            logger: 로거 (선택)
        """
        self.llm = llm
        self.logger = logger or self._setup_logger()
        self.fdr_tool = FDRTool(logger=self.logger)
        
    def _setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger("StockAnalyzer")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def analyze(
        self,
        user_query: str,
        ticker_symbols: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        주식 분석 실행
        
        Args:
            user_query: 사용자 질문 (예: "테슬라 주가 분석해줘")
            ticker_symbols: 분석할 티커 리스트 (선택, Supervisor가 제공)
                          없으면 LLM이 쿼리에서 추출
        
        Returns:
            분석 결과 딕셔너리
        """
        self.logger.info("="*50)
        self.logger.info("Stock_Analyzer 시작")
        self.logger.info("="*50)
        self.logger.info(f"사용자 요청: {user_query}")
        
        try:
            # 1. 티커 추출 (제공되지 않은 경우)
            if not ticker_symbols:
                self.logger.info("쿼리에서 티커 심볼 추출 중...")
                ticker_symbols = self._extract_tickers(user_query)
            
            if not ticker_symbols:
                return {
                    "status": "error",
                    "message": "분석할 종목을 찾을 수 없습니다. 종목명이나 티커를 명시해주세요.",
                    "data": None
                }
            
            self.logger.info(f"분석 대상 티커: {ticker_symbols}")
            
            # 2. 각 티커별 데이터 수집
            stocks_data = {}
            for ticker in ticker_symbols:
                self.logger.info(f"\n[{ticker}] 데이터 수집 중...")
                stock_data = self.fdr_tool.get_stock_data(ticker)
                
                if stock_data["status"] == "success":
                    stocks_data[ticker] = stock_data["data"]
                    self.logger.info(f"[{ticker}] 데이터 수집 완료")
                else:
                    self.logger.warning(f"[{ticker}] 데이터 수집 실패: {stock_data['message']}")
            
            if not stocks_data:
                return {
                    "status": "error",
                    "message": "주식 데이터를 가져올 수 없습니다.",
                    "data": None
                }
            
            # 3. LLM 분석
            self.logger.info("\nLLM 분석 시작...")
            analysis_result = self._analyze_with_llm(
                user_query=user_query,
                stocks_data=stocks_data
            )
            
            self.logger.info("Stock_Analyzer 완료 ✅")
            
            return {
                "status": "success",
                "message": "주식 분석이 완료되었습니다.",
                "data": {
                    "tickers": ticker_symbols,
                    "raw_data": stocks_data,
                    "analysis": analysis_result
                }
            }
            
        except Exception as e:
            self.logger.error(f"Stock_Analyzer 오류: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"분석 중 오류 발생: {str(e)}",
                "data": None
            }
    
    def analyze_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph Node 함수 - State 기반 실행
        
        Args:
            state: AgentState
        
        Returns:
            업데이트할 State
        """
        self.logger.info("="*50)
        self.logger.info("Stock_Analyzer Node 시작")
        self.logger.info("="*50)
        
        user_request = state.get("user_request", "")
        
        # Supervisor나 다른 에이전트가 이미 티커를 추출했는지 확인
        ticker_symbols = state.get("ticker_symbols", [])
        
        # 또는 companies 리스트에서 티커 매핑
        if not ticker_symbols and state.get("companies"):
            companies = state.get("companies", [])
            ticker_symbols = self._map_companies_to_tickers(companies)
        
        self.logger.info(f"State에서 가져온 티커: {ticker_symbols}")
        
        # 분석 실행
        result = self.analyze(
            user_query=user_request,
            ticker_symbols=ticker_symbols if ticker_symbols else None
        )
        
        if result["status"] == "success":
            data = result["data"]
            
            # State 업데이트
            return {
                "stock_analysis": {
                    "analysis_text": data["analysis"],
                    "summary": self._generate_summary(data),
                    "timestamp": datetime.now().isoformat()
                },
                "ticker_symbols": data["tickers"],
                "stock_data": data["raw_data"],
                "messages": [f"Stock_Analyzer: {len(data['tickers'])}개 종목 분석 완료"]
            }
        else:
            # 에러 처리
            return {
                "messages": [f"Stock_Analyzer Error: {result['message']}"]
            }
    
    def _map_companies_to_tickers(self, companies: List[str]) -> List[str]:
        """
        회사명 리스트를 티커로 변환
        
        Args:
            companies: 회사명 리스트 (예: ["LG에너지솔루션", "삼성SDI"])
        
        Returns:
            티커 리스트 (예: ["373220", "006400"])
        """
        mapping = {
            "lg에너지솔루션": "373220",
            "lges": "373220",
            "삼성sdi": "006400",
            "samsung sdi": "006400",
            "sk하이닉스": "000660",
            "sk hynix": "000660",
            "현대차": "005380",
            "hyundai": "005380",
            "기아": "000270",
            "kia": "000270",
            "테슬라": "TSLA",
            "tesla": "TSLA",
            "byd": "1211.HK",
            "포스코퓨처엠": "003670",
        }
        
        tickers = []
        for company in companies:
            company_lower = company.lower().strip()
            if company_lower in mapping:
                tickers.append(mapping[company_lower])
        
        return tickers
    
    def _generate_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        분석 결과의 요약 생성 (다른 에이전트가 활용)
        
        Args:
            data: analyze() 결과
        
        Returns:
            요약 정보
        """
        summary = {
            "analyzed_tickers": data["tickers"],
            "key_insights": [],
            "price_trends": {},
            "recommendations": []
        }
        
        # 각 티커별 핵심 정보 추출
        for ticker, stock_data in data["raw_data"].items():
            company_name = stock_data.get("company_name", ticker)
            price_info = stock_data.get("price_info", {})
            trend_info = stock_data.get("trend_analysis", {})
            
            summary["price_trends"][ticker] = {
                "company": company_name,
                "current_price": price_info.get("current_price"),
                "change_pct": price_info.get("change_pct"),
                "trend": trend_info.get("trend", "중립")
            }
            
            # 핵심 인사이트 추가
            if price_info.get("change_pct", 0) > 5:
                summary["key_insights"].append(
                    f"{company_name}: 급등세 (+{price_info.get('change_pct'):.2f}%)"
                )
            elif price_info.get("change_pct", 0) < -5:
                summary["key_insights"].append(
                    f"{company_name}: 급락세 ({price_info.get('change_pct'):.2f}%)"
                )
        
        return summary
    
    def _extract_tickers(self, query: str) -> list:
        """
        쿼리에서 티커 심볼 추출
        
        LLM을 사용하여 회사명 → 티커 변환
        """
        extraction_prompt = f"""
사용자 질문에서 주식 종목을 추출하고 티커 심볼로 변환하세요.

# 주요 전기차/배터리 기업 티커
- 테슬라: TSLA
- BYD: 1211.HK
- LG에너지솔루션: 373220
- 삼성SDI: 006400
- SK하이닉스: 000660
- 현대차: 005380
- 기아: 000270
- 포스코퓨처엠: 003670

# 사용자 질문
{query}

# 출력 형식
티커만 콤마로 구분하여 출력하세요. 설명 없이 티커만.
예: TSLA,373220,006400
"""
        
        response = self.llm.invoke([HumanMessage(content=extraction_prompt)])
        tickers_str = response.content.strip()
        
        # 파싱
        tickers = [t.strip() for t in tickers_str.split(',') if t.strip()]
        
        return tickers
    
    def _analyze_with_llm(
        self,
        user_query: str,
        stocks_data: Dict[str, Dict]
    ) -> str:
        """
        LLM을 사용한 종합 분석
        
        Args:
            user_query: 사용자 질문
            stocks_data: {ticker: data} 형태의 주식 데이터
        
        Returns:
            분석 리포트 (markdown)
        """
        # 데이터를 텍스트로 변환
        data_summary = self._format_data_for_llm(stocks_data)
        
        # 프롬프트 생성
        messages = [
            SystemMessage(content=STOCK_ANALYSIS_PROMPT),
            HumanMessage(content=f"""
# 사용자 요청
{user_query}

# 수집된 주식 데이터
{data_summary}

위 데이터를 바탕으로 사용자의 질문에 답변해주세요.
""")
        ]
        
        # LLM 호출
        response = self.llm.invoke(messages)
        
        return response.content
    
    def _format_data_for_llm(self, stocks_data: Dict[str, Dict]) -> str:
        """
        주식 데이터를 LLM이 읽기 쉬운 형태로 포맷팅
        """
        def format_number(value, default='N/A'):
            """숫자를 안전하게 포맷팅"""
            if value is None:
                return default
            try:
                return f"{float(value):,.0f}"
            except (ValueError, TypeError):
                return default
        
        def format_percent(value, default='N/A'):
            """퍼센트를 안전하게 포맷팅"""
            if value is None:
                return default
            try:
                return f"{float(value):+.2f}%"
            except (ValueError, TypeError):
                return default
        
        formatted = []
        
        for ticker, data in stocks_data.items():
            company_name = data.get("company_name", ticker)
            price_info = data.get("price_info", {})
            volume_info = data.get("volume_info", {})
            trend_info = data.get("trend_analysis", {})
            
            # 가격 정보
            current_price = format_number(price_info.get('current_price'))
            change = format_number(price_info.get('change'), '0')
            change_pct = format_percent(price_info.get('change_pct'), '0.00%')
            period_high = format_number(price_info.get('period_high'))
            period_low = format_number(price_info.get('period_low'))
            avg_price = format_number(price_info.get('avg_price'))
            
            # 거래량 정보
            recent_volume = format_number(volume_info.get('recent_volume'))
            avg_volume = format_number(volume_info.get('avg_volume'))
            volume_change = format_percent(volume_info.get('volume_change_pct'), '0.00%')
            
            # 기술적 분석
            trend = trend_info.get('trend', 'N/A')
            volatility = trend_info.get('volatility', 'N/A')
            ma20 = format_number(trend_info.get('ma20'))
            ma60 = format_number(trend_info.get('ma60'))
            
            text = f"""
## {company_name} ({ticker})

**가격 정보**
- 현재가: {current_price}원
- 전일 대비: {change}원 ({change_pct})
- 52주 최고가: {period_high}원
- 52주 최저가: {period_low}원
- 평균가(90일): {avg_price}원

**거래량**
- 최근 거래량: {recent_volume}주
- 평균 거래량: {avg_volume}주
- 거래량 변화: {volume_change}

**기술적 분석**
- 추세: {trend}
- 변동성: {volatility}
- 20일 이동평균: {ma20}원
- 60일 이동평균: {ma60}원

**데이터 기간**: {data.get('period', 'N/A')}
"""
            formatted.append(text)
        
        return "\n\n".join(formatted)