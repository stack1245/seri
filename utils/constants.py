"""상수 정의"""
from __future__ import annotations
from pathlib import Path

__all__ = [
    "DATA_DIR",
    "EMBED_COLORS",
    "AUTO_SAVE_INTERVAL",
    "DEFAULT_ACTIVITY_NAME",
    "MAX_EMBED_FIELDS",
    "MAX_FIELD_NAME_LENGTH",
    "MAX_FIELD_VALUE_LENGTH",
]

# 경로
DATA_DIR = Path(__file__).parent.parent / "data"

# 색상 (0xRRGGBB 형식)
EMBED_COLORS = {
    "RED": 0xE74C3C,
    "GREEN": 0x2ECC71,
    "BLUE": 0x3498DB,
    "YELLOW": 0xF39C12,
    "PURPLE": 0x9B59B6,
    "CYAN": 0x1ABC9C,
    "GRAY": 0x95A5A6,
    "DARK_GRAY": 0x34495E,
}

# 봇 설정
DEFAULT_ACTIVITY_NAME: str = "임베드 빌더"
AUTO_SAVE_INTERVAL: int = 300  # 5분

# 임베드 제한값
MAX_EMBED_FIELDS: int = 25
MAX_FIELD_NAME_LENGTH: int = 256
MAX_FIELD_VALUE_LENGTH: int = 1024
