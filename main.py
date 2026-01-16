"""Seri - 임베드 빌더 봇"""
from __future__ import annotations
import asyncio
import logging
import os
from typing import Optional
import discord
from dotenv import load_dotenv

from utils.extension_loader import ExtensionLoader
from utils.data_manager import DataManager
from utils.constants import AUTO_SAVE_INTERVAL, DEFAULT_ACTIVITY_NAME
from utils.graceful_shutdown import setup_graceful_shutdown, register_shutdown_callback
from utils.logging_config import configure_logging

load_dotenv()
configure_logging()
logger = logging.getLogger(__name__)


class Seri(discord.Bot):
    """임베드 빌더 봇"""

    def __init__(self):
        # Intents 설정
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            intents=intents,
            activity=discord.Activity(
                type=discord.ActivityType.competing,
                name=DEFAULT_ACTIVITY_NAME
            )
        )
        
        self.data_manager: Optional[DataManager] = None
        self._auto_save_task: Optional[asyncio.Task] = None

    async def on_ready(self) -> None:
        """봇이 준비되었을 때 호출"""
        print(f"[{self.user.name}] 준비 완료")
        
        # 데이터 로드
        if self.data_manager is None:
            self.data_manager = DataManager(self)
            self.data_manager.load_data()
        
        # 자동 저장 루프 시작
        if self._auto_save_task is None or self._auto_save_task.done():
            self._auto_save_task = asyncio.create_task(self._auto_save_loop())
        
        # 명령어 로드
        loader = ExtensionLoader(self)
        count = loader.load_extension_groups("commands")
        print(f"[{self.user.name}] {loader.get_summary()}")

    async def _auto_save_loop(self) -> None:
        """주기적으로 데이터 저장 (5분마다)"""
        await self.wait_until_ready()
        
        while not self.is_closed():
            try:
                await asyncio.sleep(AUTO_SAVE_INTERVAL)
                if self.data_manager:
                    self.data_manager.save_data()
                    logger.debug("자동 저장 완료")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"자동 저장 중 오류: {e}")

    async def on_application_command_error(
        self,
        context: discord.ApplicationContext,
        error: discord.DiscordException
    ) -> None:
        """명령어 실행 중 오류 처리"""
        logger.error(f"명령어 오류: {error}", exc_info=error)
        
        try:
            embed = discord.Embed(
                description=f"오류가 발생했습니다: {str(error)[:100]}",
                color=0xE74C3C
            )
            await context.respond(embed=embed, ephemeral=True)
        except Exception:
            pass

    async def close(self) -> None:
        """봇 종료 시 리소스 정리"""
        # 자동 저장 종료
        if self._auto_save_task and not self._auto_save_task.done():
            self._auto_save_task.cancel()
            try:
                await self._auto_save_task
            except asyncio.CancelledError:
                pass
        
        # 최종 저장
        if self.data_manager:
            self.data_manager.save_data()
            print(f"[{self.user.name}] 데이터 저장 완료")
        
        await super().close()


def main():
    """메인 진입점"""
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN이 설정되지 않았습니다.")
        return

    bot = Seri()

    # 안전한 종료 설정
    def shutdown_handler():
        asyncio.create_task(bot.close())

    register_shutdown_callback(shutdown_handler)
    setup_graceful_shutdown()

    try:
        bot.run(token)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
