"""
프로젝트 설정 관리
"""
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

# 프로젝트 루트 경로 찾기
ROOT_DIR = Path(__file__).parent.parent.parent  # common/config -> common -> EV-MARKET-ANALYSIS

class Settings(BaseSettings):
    """환경 변수 설정"""
    
    # API Keys
    OPENAI_API_KEY: str
    TAVILY_API_KEY: str
    
    # Tavily 설정
    TAVILY_MAX_RESULTS: int = 5
    
    # LLM 설정
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.0
    
    # 로깅
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = str(ROOT_DIR / ".env")  # 절대 경로 지정
        env_file_encoding = "utf-8"

# 전역 settings 객체
settings = Settings()