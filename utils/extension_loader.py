"""확장 로더"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import List
import discord

logger = logging.getLogger(__name__)

__all__ = ["ExtensionLoader"]


class ExtensionLoader:
    """Discord Bot 확장(명령어) 로더"""

    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.loaded_extensions: List[str] = []
        self.failed_extensions: List[tuple[str, str]] = []

    def load_extensions(self, extensions_dir: str | Path) -> int:
        """디렉토리에서 모든 확장 로드
        
        Args:
            extensions_dir: 확장 디렉토리 경로
            
        Returns:
            로드된 확장 개수
        """
        extensions_path = Path(extensions_dir)
        
        if not extensions_path.exists():
            logger.warning(f"확장 디렉토리 없음: {extensions_path}")
            return 0

        count = 0
        
        # 폴더의 모든 .py 파일 스캔
        for file_path in sorted(extensions_path.glob("*.py")):
            if file_path.name.startswith("_"):
                continue
                
            module_name = file_path.stem
            extension_name = f"{extensions_path.name}.{module_name}"
            
            try:
                self.bot.load_extension(extension_name)
                self.loaded_extensions.append(extension_name)
                count += 1
            except Exception as e:
                self.failed_extensions.append((extension_name, str(e)))
                logger.error(f"확장 로드 실패: {extension_name} - {e}")

        return count

    def load_extension_groups(self, extensions_dir: str | Path) -> int:
        """확장 그룹 로드 (서브폴더)
        
        Args:
            extensions_dir: 확장 디렉토리 경로
            
        Returns:
            로드된 확장 개수
        """
        extensions_path = Path(extensions_dir)
        count = self.load_extensions(extensions_path)

        # 서브폴더 처리
        for subdir in sorted(extensions_path.iterdir()):
            if subdir.is_dir() and not subdir.name.startswith("_"):
                init_file = subdir / "__init__.py"
                if init_file.exists():
                    parent_name = extensions_path.name
                    extension_name = f"{parent_name}.{subdir.name}"
                    
                    try:
                        self.bot.load_extension(extension_name)
                        self.loaded_extensions.append(extension_name)
                        count += 1
                    except Exception as e:
                        self.failed_extensions.append((extension_name, str(e)))
                        logger.error(f"확장 로드 실패: {extension_name} - {e}")

        return count

    def get_summary(self) -> str:
        """로딩 요약 정보
        
        Returns:
            요약 정보 문자열
        """
        summary = f"로드된 확장: {len(self.loaded_extensions)}개"
        
        if self.failed_extensions:
            summary += f", 실패: {len(self.failed_extensions)}개"
        
        return summary
