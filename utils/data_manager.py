"""JSON 파일 기반 데이터 관리"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any
import discord

from .constants import DATA_DIR

logger = logging.getLogger(__name__)

__all__ = ["DataManager"]


class DataManager:
    """사용자 임베드 데이터 관리"""

    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.embeds_file = DATA_DIR / "embeds.json"
        self.user_embeds: dict[int, dict[str, Any]] = {}
        
        # 디렉토리 생성
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def load_data(self) -> None:
        """모든 데이터 로드"""
        self._load_embeds()

    def save_data(self) -> None:
        """모든 데이터 저장"""
        self._save_embeds()

    def _load_embeds(self) -> None:
        """사용자 임베드 로드"""
        try:
            if self.embeds_file.exists():
                with open(self.embeds_file, "r", encoding="utf-8") as f:
                    self.user_embeds = json.load(f)
            else:
                self.user_embeds = {}
                self._save_embeds()
        except Exception as e:
            logger.error(f"임베드 로드 실패: {e}")
            self.user_embeds = {}

    def _save_embeds(self) -> None:
        """사용자 임베드 저장"""
        try:
            with open(self.embeds_file, "w", encoding="utf-8") as f:
                json.dump(self.user_embeds, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"임베드 저장 실패: {e}")

    def save_embed(self, user_id: int, embed_name: str, embed_data: dict[str, Any]) -> None:
        """임베드 저장
        
        Args:
            user_id: 사용자 ID
            embed_name: 임베드 이름
            embed_data: 임베드 데이터
        """
        if user_id not in self.user_embeds:
            self.user_embeds[user_id] = {}
        
        self.user_embeds[user_id][embed_name] = embed_data
        self._save_embeds()

    def get_embed(self, user_id: int, embed_name: str) -> dict[str, Any] | None:
        """임베드 조회
        
        Args:
            user_id: 사용자 ID
            embed_name: 임베드 이름
            
        Returns:
            임베드 데이터 (없으면 None)
        """
        if user_id not in self.user_embeds:
            return None
        return self.user_embeds[user_id].get(embed_name)

    def delete_embed(self, user_id: int, embed_name: str) -> bool:
        """임베드 삭제
        
        Args:
            user_id: 사용자 ID
            embed_name: 임베드 이름
            
        Returns:
            성공 여부
        """
        if user_id not in self.user_embeds:
            return False
        
        if embed_name in self.user_embeds[user_id]:
            del self.user_embeds[user_id][embed_name]
            self._save_embeds()
            return True
        return False

    def list_embeds(self, user_id: int) -> list[str]:
        """사용자의 모든 임베드 이름 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            임베드 이름 목록
        """
        if user_id not in self.user_embeds:
            return []
        return list(self.user_embeds[user_id].keys())

    def embed_exists(self, user_id: int, embed_name: str) -> bool:
        """임베드 존재 여부 확인
        
        Args:
            user_id: 사용자 ID
            embed_name: 임베드 이름
            
        Returns:
            존재 여부
        """
        if user_id not in self.user_embeds:
            return False
        return embed_name in self.user_embeds[user_id]
