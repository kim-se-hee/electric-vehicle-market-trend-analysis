"""
Stock Analyzer Agent 테스트
"""
import os
import sys
import json
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
# test/ -> stock_analysis/ -> ev-market-analysis/
project_root = Path(__file__).parent.parent.parent  # ev-market-analysis/
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from stock_analysis.agent.stock_analyzer import StockAnalyzerAgent

# 환경 변수 로드
load_dotenv()

def test_single_stock():
    """단일 종목 분석 테스트"""
    print("\n" + "="*60)
    print("🧪 테스트 1: 단일 종목 분석 (LG에너지솔루션)")
    print("="*60)
    
    # LLM 초기화
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )
    
    # 에이전트 초기화
    agent = StockAnalyzerAgent(llm=llm)
    
    # 분석 실행
    result = agent.analyze(
        user_query="LG에너지솔루션 주식 분석해줘",
        ticker_symbols=["373220"]  # Supervisor가 제공하는 경우
    )
    
    # 결과 출력
    print(f"\n📊 상태: {result['status']}")
    print(f"📝 메시지: {result['message']}")
    
    if result['status'] == 'success':
        print(f"\n✅ 분석 완료!")
        print(f"분석 대상: {result['data']['tickers']}")
        print("\n" + "="*60)
        print("📈 분석 리포트")
        print("="*60)
        print(result['data']['analysis'])
        
        # JSON 저장
        with open('stock_analysis_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 결과가 'stock_analysis_result.json'에 저장되었습니다.")


def test_multiple_stocks():
    """복수 종목 비교 분석 테스트"""
    print("\n" + "="*60)
    print("🧪 테스트 2: 복수 종목 비교 (배터리 3사)")
    print("="*60)
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = StockAnalyzerAgent(llm=llm)
    
    result = agent.analyze(
        user_query="LG에너지솔루션, 삼성SDI, SK이노베이션 배터리 3사 비교 분석해줘",
        ticker_symbols=["373220", "006400", "096770"]
    )
    
    print(f"\n📊 상태: {result['status']}")
    
    if result['status'] == 'success':
        print("\n" + "="*60)
        print("📈 비교 분석 리포트")
        print("="*60)
        print(result['data']['analysis'])


def test_ticker_extraction():
    """티커 자동 추출 테스트 (Supervisor가 티커를 제공하지 않는 경우)"""
    print("\n" + "="*60)
    print("🧪 테스트 3: 티커 자동 추출")
    print("="*60)
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = StockAnalyzerAgent(llm=llm)
    
    # 티커를 명시하지 않고 회사명으로 질문
    result = agent.analyze(
        user_query="테슬라랑 현대차 주가 비교해줘"
        # ticker_symbols 제공 안 함 → LLM이 자동 추출
    )
    
    print(f"\n📊 상태: {result['status']}")
    
    if result['status'] == 'success':
        print(f"🎯 추출된 티커: {result['data']['tickers']}")
        print("\n" + "="*60)
        print("📈 분석 리포트")
        print("="*60)
        print(result['data']['analysis'])


def test_supervisor_scenario():
    """
    Supervisor 시나리오 시뮬레이션
    
    Supervisor가 쿼리를 분석하고:
    1. 특정 기업 관련 질문이면 → Stock_Analyzer 호출
    2. 일반 시장 질문이면 → Stock_Analyzer 호출 안 함
    """
    print("\n" + "="*60)
    print("🧪 테스트 4: Supervisor 시나리오")
    print("="*60)
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = StockAnalyzerAgent(llm=llm)
    
    # 시나리오 1: 특정 기업 질문 → Stock_Analyzer 호출
    print("\n[시나리오 1] 사용자: '삼성SDI 주가 어때?'")
    print("→ Supervisor 판단: 특정 기업 관련 → Stock_Analyzer 호출")
    
    result1 = agent.analyze(
        user_query="삼성SDI 주가 최근 어때? 투자할 만해?",
        ticker_symbols=["006400"]
    )
    
    if result1['status'] == 'success':
        print(f"\n✅ Stock_Analyzer 결과:")
        print(result1['data']['analysis'][:300] + "...")
    
    # 시나리오 2: 일반 시장 질문 → Stock_Analyzer 불필요
    print("\n" + "-"*60)
    print("\n[시나리오 2] 사용자: '전기차 시장 전망은?'")
    print("→ Supervisor 판단: 일반 시장 질문 → Market_Researcher만 호출")
    print("→ Stock_Analyzer는 호출되지 않음")


if __name__ == "__main__":
    # API 키 확인
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        print("📝 .env 파일에 OPENAI_API_KEY를 추가해주세요.")
        exit(1)
    
    print("\n" + "🚀"*30)
    print("Stock Analyzer Agent 테스트 시작")
    print("🚀"*30)
    
    # 테스트 실행
    try:
        # 1. 단일 종목
        test_single_stock()
        
        # 2. 복수 종목 (선택)
        # test_multiple_stocks()
        
        # 3. 티커 자동 추출 (선택)
        # test_ticker_extraction()
        
        # 4. Supervisor 시나리오 (선택)
        # test_supervisor_scenario()
        
        print("\n" + "✅"*30)
        print("모든 테스트 완료!")
        print("✅"*30 + "\n")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()