"""
Market Researcher Agent 테스트 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent.parent  # 3단계 위로
sys.path.insert(0, str(project_root))

from market_research.agent.market_researcher import MarketResearcherAgent
import json

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🚗 전기차 시장 조사 에이전트 테스트")
    print("=" * 60)
    
    # 에이전트 초기화
    agent = MarketResearcherAgent()
    
    # 초기 상태 설정
    initial_state = {
        "user_request": "전기차 시장 동향과 주요 기업 분석해줘",
        "messages": [],
        "references": []
    }
    
    print("\n📋 사용자 요청:", initial_state["user_request"])
    print("\n🔍 시장 조사 시작...\n")
    
    # 에이전트 실행
    try:
        result = agent.run(initial_state)
        
        print("\n" + "=" * 60)
        print("✅ 시장 조사 완료!")
        print("=" * 60)
        
        # 결과 출력
        market_data = result.get("market_research", {})
        
        print("\n📊 시장 요약:")
        print("-" * 60)
        print(market_data.get("summary", "N/A"))
        
        print("\n💰 시장 규모:", market_data.get("market_size", "N/A"))
        print("📈 성장률:", market_data.get("growth_rate", "N/A"))
        
        print("\n🔥 주요 트렌드:")
        print("-" * 60)
        for i, trend in enumerate(market_data.get("key_trends", []), 1):
            if isinstance(trend, dict):
                print(f"{i}. {trend.get('title', 'N/A')} [{trend.get('impact', 'N/A')}]")
                print(f"   → {trend.get('description', 'N/A')}")
            else:
                print(f"{i}. {trend}")
        
        print("\n⚠️ 리스크 요인:")
        print("-" * 60)
        for i, risk in enumerate(market_data.get("risks", []), 1):
            if isinstance(risk, dict):
                print(f"{i}. {risk.get('title', 'N/A')} [심각도: {risk.get('severity', 'N/A')}]")
                print(f"   → {risk.get('description', 'N/A')}")
            else:
                print(f"{i}. {risk}")
        
        print("\n🔋 배터리 공급망:")
        print("-" * 60)
        print(market_data.get("battery_supply_chain", "N/A"))
        
        print("\n📚 참고 문헌:")
        print("-" * 60)
        for i, url in enumerate(result.get("references", [])[:5], 1):
            print(f"{i}. {url}")
        
        # JSON 파일로 저장 (HumanMessage 객체 제외)
        output_file = "market_research_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            result_to_save = {
                "market_research": result.get("market_research", {}),
                "references": result.get("references", [])
            }
            json.dump(result_to_save, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 전체 결과가 '{output_file}'에 저장되었습니다.")
        
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()