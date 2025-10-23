"""
Base Agent 클래스
모든 에이전트가 상속받는 기본 클래스
"""
from langchain_openai import ChatOpenAI
from common.config.settings import settings
import logging
from typing import Dict, Any

class BaseAgent:
    """모든 에이전트의 베이스 클래스"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = self._setup_logger()
        self.llm = self._setup_llm()
    
    def _setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'[%(asctime)s] {self.name} - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _setup_llm(self) -> ChatOpenAI:
        """LLM 설정"""
        return ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            api_key=settings.OPENAI_API_KEY
        )
    
    def log_start(self):
        """에이전트 시작 로그"""
        self.logger.info(f"{'='*50}")
        self.logger.info(f"{self.name} 시작")
        self.logger.info(f"{'='*50}")
    
    def log_complete(self):
        """에이전트 완료 로그"""
        self.logger.info(f"{self.name} 완료 ✅")
    
    def handle_error(self, error: Exception, state: Dict) -> Dict:
        """에러 처리"""
        self.logger.error(f"❌ 에러 발생: {error}", exc_info=True)
        return {
            "error": str(error),
            "agent": self.name,
            "messages": state.get("messages", [])
        }
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        에이전트 실행 (서브클래스에서 구현)
        
        Args:
            state: 현재 상태
            
        Returns:
            업데이트된 상태
        """
        raise NotImplementedError("Subclass must implement run() method")