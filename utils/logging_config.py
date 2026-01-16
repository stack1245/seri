"""로깅 설정"""
from __future__ import annotations
import logging
import sys


def configure_logging(level: int = logging.INFO, log_file: bool = False) -> None:
    """로깅 설정
    
    Args:
        level: 로깅 레벨 (기본값: INFO)
        log_file: 파일에 저장 여부 (기본값: False)
    """
    # 기본 포맷
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    
    # 비동기 관련 로그 조용히
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
