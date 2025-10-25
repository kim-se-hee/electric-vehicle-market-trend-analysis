"""
FinanceDataReader Tool
주식 데이터 수집 및 캐싱
"""
import os
import pickle
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

import pandas as pd
import FinanceDataReader as fdr


class FDRTool:
    """
    FinanceDataReader 기반 주식 데이터 수집 도구
    
    특징:
    - Rate Limit 없음 (yfinance 대비)
    - 한국/미국 주식 지원
    - 자동 캐싱 (2시간)
    - 재시도 로직
    """
    
    def __init__(
        self,
        cache_dir: str = "./cache",
        cache_hours: int = 2,
        max_retries: int = 3,
        logger: Optional[logging.Logger] = None
    ):
        """
        Args:
            cache_dir: 캐시 디렉토리
            cache_hours: 캐시 유효 시간 (시간)
            max_retries: 최대 재시도 횟수
            logger: 로거
        """
        self.cache_dir = cache_dir
        self.cache_hours = cache_hours
        self.max_retries = max_retries
        self.logger = logger or logging.getLogger(__name__)
        
        # 캐시 디렉토리 생성
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_stock_data(
        self,
        ticker: str,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        주식 데이터 가져오기
        
        Args:
            ticker: 티커 심볼
                   한국: "000660" (SK하이닉스)
                   미국: "TSLA" (테슬라)
            days: 조회 기간 (일)
        
        Returns:
            {
                "status": "success" | "error",
                "message": str,
                "data": {...} | None
            }
        """
        try:
            # 날짜 범위
            end_date = datetime.today()
            start_date = end_date - timedelta(days=days)
            
            # 캐시 확인
            cached_data = self._get_cached_data(ticker, start_date, end_date)
            if cached_data is not None:
                self.logger.info(f"[{ticker}] 캐시 데이터 사용")
                return {
                    "status": "success",
                    "message": "캐시에서 데이터를 불러왔습니다.",
                    "data": cached_data
                }
            
            # 데이터 가져오기 (재시도 포함)
            df = self._fetch_with_retry(ticker, start_date, end_date)
            
            if df.empty:
                return {
                    "status": "error",
                    "message": f"[{ticker}] 데이터를 찾을 수 없습니다. 티커를 확인해주세요.",
                    "data": None
                }
            
            # 데이터 분석
            analyzed_data = self._analyze_dataframe(df, ticker)
            
            # 캐시 저장
            self._save_to_cache(ticker, start_date, end_date, analyzed_data)
            
            return {
                "status": "success",
                "message": "데이터를 성공적으로 가져왔습니다.",
                "data": analyzed_data
            }
            
        except Exception as e:
            self.logger.error(f"[{ticker}] 오류: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"데이터 수집 중 오류: {str(e)}",
                "data": None
            }
    
    def _fetch_with_retry(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """재시도 로직이 포함된 데이터 가져오기"""
        import time
        
        for attempt in range(self.max_retries):
            try:
                self.logger.info(
                    f"[{ticker}] 데이터 조회 중... (시도 {attempt + 1}/{self.max_retries})"
                )
                
                df = fdr.DataReader(ticker, start_date, end_date)
                
                if not df.empty:
                    return df
                else:
                    self.logger.warning(f"[{ticker}] 데이터가 비어있습니다.")
                    if attempt < self.max_retries - 1:
                        time.sleep(1)
                        
            except Exception as e:
                self.logger.warning(f"[{ticker}] 시도 {attempt + 1} 실패: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
        
        return pd.DataFrame()
    
    def _analyze_dataframe(self, df: pd.DataFrame, ticker: str) -> Dict[str, Any]:
        """
        DataFrame 분석하여 구조화된 데이터 반환
        """
        # 기본 정보
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
        change = current_price - prev_price
        change_pct = (change / prev_price * 100) if prev_price != 0 else 0
        
        # 가격 정보
        price_info = {
            "current_price": float(current_price),
            "prev_price": float(prev_price),
            "change": float(change),
            "change_pct": float(change_pct),
            "period_high": float(df['Close'].max()),
            "period_low": float(df['Close'].min()),
            "avg_price": float(df['Close'].mean())
        }
        
        # 거래량 정보
        volume_info = {}
        if 'Volume' in df.columns:
            recent_volume = df['Volume'].iloc[-1]
            avg_volume = df['Volume'].mean()
            volume_change_pct = ((recent_volume / avg_volume - 1) * 100) if avg_volume != 0 else 0
            
            volume_info = {
                "recent_volume": int(recent_volume),
                "avg_volume": float(avg_volume),
                "volume_change_pct": float(volume_change_pct)
            }
        
        # 추세 분석
        trend_info = self._calculate_trend(df)
        
        # 기간 정보
        period = f"{df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}"
        
        return {
            "ticker": ticker,
            "company_name": self._get_company_name(ticker),
            "price_info": price_info,
            "volume_info": volume_info,
            "trend_analysis": trend_info,
            "period": period,
            "data_points": len(df),
            "last_updated": datetime.now().isoformat()
        }
    
    def _calculate_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """기술적 분석 - 추세 계산"""
        close_prices = df['Close']
        
        # 이동평균
        ma20 = close_prices.rolling(window=20).mean().iloc[-1] if len(df) >= 20 else None
        ma60 = close_prices.rolling(window=60).mean().iloc[-1] if len(df) >= 60 else None
        
        # 추세 판단
        current = close_prices.iloc[-1]
        trend = "중립"
        if ma20 and ma60:
            if current > ma20 > ma60:
                trend = "강한 상승"
            elif current > ma20:
                trend = "상승"
            elif current < ma20 < ma60:
                trend = "강한 하락"
            elif current < ma20:
                trend = "하락"
        
        # 변동성 (표준편차)
        volatility = float(close_prices.pct_change().std() * 100)  # %
        
        return {
            "trend": trend,
            "ma20": float(ma20) if ma20 else None,
            "ma60": float(ma60) if ma60 else None,
            "volatility": f"{volatility:.2f}%"
        }
    
    def _get_company_name(self, ticker: str) -> str:
        """티커 → 회사명 매핑"""
        mapping = {
            # 한국
            "373220": "LG에너지솔루션",
            "006400": "삼성SDI",
            "000660": "SK하이닉스",
            "005380": "현대차",
            "000270": "기아",
            "003670": "포스코퓨처엠",
            
            # 미국
            "TSLA": "Tesla",
            "AAPL": "Apple",
            "MSFT": "Microsoft",
            
            # 중국/홍콩
            "1211.HK": "BYD"
        }
        
        return mapping.get(ticker, ticker)
    
    def _get_cached_data(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """캐시에서 데이터 가져오기"""
        cache_file = self._get_cache_filename(ticker, start_date, end_date)
        
        if not os.path.exists(cache_file):
            return None
        
        # 캐시 유효성 확인
        cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - cache_time > timedelta(hours=self.cache_hours):
            self.logger.info(f"[{ticker}] 캐시 만료됨")
            return None
        
        # 캐시 로드
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            self.logger.warning(f"[{ticker}] 캐시 로드 실패: {e}")
            return None
    
    def _save_to_cache(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime,
        data: Dict[str, Any]
    ):
        """데이터를 캐시에 저장"""
        cache_file = self._get_cache_filename(ticker, start_date, end_date)
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            self.logger.info(f"[{ticker}] 캐시 저장 완료: {cache_file}")
        except Exception as e:
            self.logger.warning(f"[{ticker}] 캐시 저장 실패: {e}")
    
    def _get_cache_filename(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """캐시 파일명 생성"""
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')
        return os.path.join(
            self.cache_dir,
            f"fdr_{ticker}_{start_str}_{end_str}.pkl"
        )