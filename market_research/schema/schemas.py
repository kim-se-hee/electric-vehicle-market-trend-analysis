"""
Market Research 데이터 스키마
"""

from pydantic import BaseModel, Field
from typing import List, Optional

class TrendItem(BaseModel):
    """시장 트렌드 항목"""
    title: str = Field(description="트렌드 제목")
    description: str = Field(description="상세 설명")
    impact: str = Field(description="영향도: 긍정적|부정적|중립적")

class RiskItem(BaseModel):
    """리스크 항목"""
    title: str = Field(description="리스크 제목")
    description: str = Field(description="상세 설명")
    severity: str = Field(description="심각도: 높음|중간|낮음")

class MarketResearchOutput(BaseModel):
    """시장 조사 최종 결과"""
    summary: str = Field(description="시장 전체 요약")
    market_size: Optional[str] = Field(default=None, description="현재 시장 규모")
    growth_rate: str = Field(description="예상 성장률")
    key_companies: List[str] = Field(default_factory=list, description="주요 기업 리스트")
    key_trends: List[dict] = Field(default_factory=list, description="주요 트렌드")
    opportunities: List[str] = Field(default_factory=list, description="시장 기회")
    risks: List[dict] = Field(default_factory=list, description="리스크 요인")
    battery_supply_chain: Optional[str] = Field(default=None, description="배터리 공급망 현황")
    sources: List[str] = Field(default_factory=list, description="참고 자료 URL")