"""
Company Analyzer Agent 테스트 스크립트
Market Researcher의 결과를 받아서 기업 분석 수행
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from market_research.agent.market_researcher import MarketResearcherAgent
from company_analysis.agent.company_analyzer import CompanyAnalyzerAgent
import json


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🔗 통합 테스트: Market Research → Company Analysis")
    print("=" * 60)
    
    print("\n" + "="*60)
    print("STEP 1: 시장 조사")
    print("="*60)
    
    market_agent = MarketResearcherAgent()
    
    initial_state = {
        "user_request": "전기차 시장 동향과 주요 기업 분석해줘",
        "messages": [],
        "references": [],
        "companies": []
    }
    
    print(f"\n📋 사용자 요청: {initial_state['user_request']}")
    print("\n🔍 Market Research 시작...\n")
    
    try:
        state_after_market = market_agent.run(initial_state)
        
        print("\n✅ Market Research 완료!")
        
        market_data = state_after_market.get("market_research", {})
        companies = state_after_market.get("companies", [])
        
        print(f"\n📊 발견된 주요 기업 (State): {companies}")
        print(f"📊 발견된 주요 기업 (market_research): {market_data.get('key_companies', [])}")
        print(f"📚 수집한 참고자료: {len(state_after_market.get('references', []))}개")
        
        print("\n" + "="*60)
        print("STEP 2: 기업 분석")
        print("="*60)
        
        company_agent = CompanyAnalyzerAgent()
        
        print("\n🔍 Company Analysis 시작...\n")
        
        final_state = company_agent.run(state_after_market)
        
        print("\n" + "=" * 60)
        print("✅ 전체 분석 완료!")
        print("=" * 60)
        
        company_analyses = final_state.get("company_analysis", {})
        
        for company, analysis in company_analyses.items():
            print(f"\n{'='*60}")
            print(f"🏢 {company}")
            print(f"{'='*60}")
            print(analysis.get("summary_analysis", "N/A"))
            print()
        
        output_file = "integrated_analysis_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            result_to_save = {
                "market_research": final_state.get("market_research", {}),
                "companies": final_state.get("companies", []),
                "company_analysis": company_analyses,
                "references": final_state.get("references", []),
                "market_research_done": final_state.get("market_research_done", False),
                "company_analysis_done": final_state.get("company_analysis_done", False)
            }
            json.dump(result_to_save, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 결과 저장: {output_file}")
        
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()