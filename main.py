"""Seri - 임베드 빌더 봇"""
from __future__ import annotations
import asyncio
import os
import sys

import discord
from dotenv import load_dotenv

from utils.extension_loader import ExtensionLoader
from utils.data_manager import DataManager
from utils.constants import AUTO_SAVE_INTERVAL, DEFAULT_ACTIVITY_NAME
from utils.graceful_shutdown import setup_graceful_shutdown, register_shutdown_callback
from utils.logging_config import configure_logging

load_dotenv()
configure_logging()

import logging
logger = logging.getLogger(__name__)


class Seri(discord.Bot):
    """임베드 빌더 봇"""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(intents=intents)
        
        self.data_manager = DataManager(self)
        self.extension_loader = ExtensionLoader(self)
        self._initialized = False
        self._auto_save_task: asyncio.Task | None = None

    async def on_ready(self) -> None:
        """봇 준비 완료"""
        if self._initialized or not self.user:
            return
        
        try:
            await self._initialize()
            self._initialized = True
            print(f"[{self.user.name}] 준비 완료")
        except Exception as e:
            logger.error(f"초기화 실패: {e}", exc_info=e)
            await self.close()

    async def _initialize(self) -> None:
        """초기화 로직"""
        self.data_manager.load_data()
        
        self.extension_loader.load_extension_groups("commands")
        if self.extension_loader.failed_extensions:
            for ext_name, error in self.extension_loader.failed_extensions:
                logger.error(f"명령어 로드 실패: {ext_name}\n{error}")
        
        if self._auto_save_task is None or self._auto_save_task.done():
            self._auto_save_task = asyncio.create_task(self._auto_save_loop())
        
        try:
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.unknown,
                    name=DEFAULT_ACTIVITY_NAME
                )
            )
        except Exception as e:
            logger.error(f"상태 변경 오류: {e}")

    async def _auto_save_loop(self) -> None:
        """주기적 데이터 저장"""
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                await asyncio.sleep(AUTO_SAVE_INTERVAL)
                self.data_manager.save_data()
                logger.debug("자동 저장 완료")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"자동 저장 오류: {e}")

    async def on_application_command_error(
        self,
        context: discord.ApplicationContext,
        error: discord.DiscordException
    ) -> None:
        """명령어 오류 처리"""
        logger.error(f"명령어 오류: {error}", exc_info=error)
        
        try:
            embed = discord.Embed(
                description=f"오류 발생: {str(error)[:100]}",
                color=0xE74C3C
            )
            if not context.response.is_done():
                await context.respond(embed=embed, ephemeral=True)
        except Exception:
            pass

    async def close(self) -> None:
        """봇 종료 처리"""
        if self._auto_save_task and not self._auto_save_task.done():
            self._auto_save_task.cancel()
            try:
                await self._auto_save_task
            except asyncio.CancelledError:
                pass
        
        if self.data_manager:
            self.data_manager.save_data()
            logger.debug("종료 전 데이터 저장")
        
        await super().close()


def main() -> None:
    """봇 실행"""
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN 미설정")
        return

    bot = Seri()

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
