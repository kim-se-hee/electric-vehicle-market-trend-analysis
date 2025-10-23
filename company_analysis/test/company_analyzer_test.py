"""
Company Analyzer Agent 테스트 스크립트
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from company_analysis.agent.company_analyzer import CompanyAnalyzerAgent
import json


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🏢 기업 분석 에이전트 테스트")
    print("=" * 60)
    
    # 에이전트 초기화
    agent = CompanyAnalyzerAgent()
    
    # 초기 상태 설정 (Market Research 완료 후 상태를 시뮬레이션)
    initial_state = {
        "user_request": "전기차 주요 기업 분석해줘",
        "messages": [],
        "market_research": {
            "major_players": [
                "Tesla",
                "BYD",
                "Samsung SDI"
            ]
        },
        "market_research_done": True
    }
    
    print("\n📋 분석 대상:", ", ".join(initial_state["market_research"]["major_players"]))
    print("\n🔍 기업 분석 시작...\n")
    
    # 에이전트 실행
    try:
        result = agent.run(initial_state)
        
        print("\n" + "=" * 60)
        print("✅ 기업 분석 완료!")
        print("=" * 60)
        
        # 결과 출력
        company_analyses = result.get("company_analysis", {})
        
        for company, analysis in company_analyses.items():
            print(f"\n{'='*60}")
            print(f"🏢 {company}")
            print(f"{'='*60}")
            print(analysis.get("summary_analysis", "N/A"))
            print()
        
        # JSON 파일로 저장
        output_file = "company_analysis_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            # 저장할 데이터 준비
            result_to_save = {
                "company_analysis": company_analyses,
                "company_analysis_done": result.get("company_analysis_done", False)
            }
            json.dump(result_to_save, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 결과 저장: {output_file}")
        
        # 참고: 실제로는 벡터 DB도 저장 가능
        # agent.rag_tool.save_vectorstore("./vectorstore")
        
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()