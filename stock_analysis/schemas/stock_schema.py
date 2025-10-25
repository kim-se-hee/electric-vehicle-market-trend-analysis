"""
Stock Analysis Schemas
주식 분석 결과의 데이터 구조
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class PriceInfo(BaseModel):
    """가격 정보"""
    current_price: float = Field(..., description="현재가")
    prev_price: float = Field(..., description="전일 종가")
    change: float = Field(..., description="전일 대비 변화")
    change_pct: float = Field(..., description="전일 대비 변화율 (%)")
    period_high: float = Field(..., description="기간 최고가")
    period_low: float = Field(..., description="기간 최저가")
    avg_price: float = Field(..., description="평균가")


class VolumeInfo(BaseModel):
    """거래량 정보"""
    recent_volume: int = Field(..., description="최근 거래량")
    avg_volume: float = Field(..., description="평균 거래량")
    volume_change_pct: float = Field(..., description="거래량 변화율 (%)")


class TrendAnalysis(BaseModel):
    """추세 분석"""
    trend: str = Field(..., description="추세 (상승/하락/중립)")
    ma20: Optional[float] = Field(None, description="20일 이동평균")
    ma60: Optional[float] = Field(None, description="60일 이동평균")
    volatility: str = Field(..., description="변동성")


class StockData(BaseModel):
    """주식 데이터"""
    ticker: str = Field(..., description="티커 심볼")
    company_name: str = Field(..., description="회사명")
    price_info: PriceInfo = Field(..., description="가격 정보")
    volume_info: VolumeInfo = Field(..., description="거래량 정보")
    trend_analysis: TrendAnalysis = Field(..., description="추세 분석")
    period: str = Field(..., description="데이터 기간")
    data_points: int = Field(..., description="데이터 포인트 수")
    last_updated: str = Field(..., description="마지막 업데이트")


class StockAnalysisResult(BaseModel):
    """주식 분석 최종 결과"""
    status: str = Field(..., description="상태 (success/error)")
    message: str = Field(..., description="메시지")
    data: Optional[Dict[str, Any]] = Field(None, description="분석 결과 데이터")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "주식 분석이 완료되었습니다.",
                "data": {
                    "tickers": ["TSLA", "373220"],
                    "raw_data": {},
                    "analysis": "분석 리포트..."
                }
            }
        }