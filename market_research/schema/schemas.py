from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class TrendItem(BaseModel):
    """개별 트렌드 항목"""
    title: str = Field(description="트렌드 제목")
    description: str = Field(description="트렌드 상세 설명")
    impact: str = Field(description="시장에 미치는 영향 (긍정적/부정적/중립적)")

class RiskItem(BaseModel):
    """리스크 항목"""
    title: str = Field(description="리스크 제목")
    description: str = Field(description="리스크 상세 설명")
    severity: str = Field(description="심각도 (높음/중간/낮음)")

class MarketResearchOutput(BaseModel):
    """시장 조사 결과 데이터 모델"""
    summary: str = Field(description="시장 전체 요약 (3-5문장)")
    market_size: Optional[str] = Field(default=None, description="현재 시장 규모")
    growth_rate: str = Field(description="예상 성장률 (예: 12% YoY)")
    key_trends: List[TrendItem] = Field(description="주요 트렌드 3-5개")
    opportunities: List[str] = Field(default=[], description="시장 기회 요인")
    risks: List[RiskItem] = Field(description="리스크 요인 2-3개")
    battery_supply_chain: Optional[str] = Field(default=None, description="리튬 배터리 공급망 현황")
    sources: List[str] = Field(description="참고 문헌 URL 리스트")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    class Config:
        json_schema_extra = {
            "example": {
                "summary": "2025년 전기차 시장은 성장세를 유지하고 있으나...",
                "market_size": "1.2조 달러",
                "growth_rate": "12% YoY",
                "key_trends": [
                    {
                        "title": "가격 경쟁 심화",
                        "description": "중국 제조사들의 공격적인 가격 정책으로 시장 경쟁 심화",
                        "impact": "부정적"
                    }
                ],
                "opportunities": ["신흥 시장 진출", "배터리 재활용 사업"],
                "risks": [
                    {
                        "title": "정부 보조금 감소",
                        "description": "주요 국가들의 보조금 축소 정책",
                        "severity": "높음"
                    }
                ],
                "battery_supply_chain": "리튬 공급 부족 우려 지속",
                "sources": ["https://example.com/ev-market"],
                "timestamp": "2025-10-22T10:30:00"
            }
        }