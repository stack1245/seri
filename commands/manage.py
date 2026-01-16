"""임베드 관리 명령어"""
from __future__ import annotations
import json
import logging
from typing import Optional
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class ManageCommand(commands.Cog):
    """임베드 관리 명령어"""

    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.slash_command(name="list", description="저장된 임베드 목록을 확인합니다")
    async def list_embeds(self, ctx: discord.ApplicationContext) -> None:
        """저장된 임베드 목록"""
        if not self.bot.data_manager:
            embed = discord.Embed(
                description="데이터 관리자가 초기화되지 않았습니다.",
                color=0xE74C3C
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        embed_names = self.bot.data_manager.list_embeds(ctx.user.id)
        
        if not embed_names:
            embed = discord.Embed(
                description="저장된 임베드가 없습니다. `/create` 명령어로 새로운 임베드를 만들어보세요.",
                color=0x3498DB
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        # 목록 표시
        view = EmbedListView(self.bot, ctx.user.id, embed_names)
        embed = discord.Embed(
            title="저장된 임베드 목록",
            description="\n".join([f"• {name}" for name in embed_names]),
            color=0x3498DB
        )
        embed.set_footer(text=f"총 {len(embed_names)}개")
        
        await ctx.respond(embed=embed, view=view, ephemeral=True)

    @discord.slash_command(name="load", description="저장된 임베드를 불러옵니다")
    async def load_embed(self, ctx: discord.ApplicationContext, name: str) -> None:
        """임베드 불러오기"""
        if not self.bot.data_manager:
            embed = discord.Embed(
                description="데이터 관리자가 초기화되지 않았습니다.",
                color=0xE74C3C
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        embed_data = self.bot.data_manager.get_embed(ctx.user.id, name)
        
        if not embed_data:
            embed = discord.Embed(
                description=f"'{name}'이라는 임베드를 찾을 수 없습니다.",
                color=0xE74C3C
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        
        # 임베드 생성
        loaded_embed = self._create_embed(embed_data)
        view = LoadedEmbedView(loaded_embed, embed_data, self.bot, ctx.user.id, name)
        
        info_embed = discord.Embed(
            title=f"'{name}' 불러옴",
            description="아래 임베드를 확인하거나 수정할 수 있습니다.",
            color=0x2ECC71
        )
        
        await ctx.respond(embed=info_embed, ephemeral=True)
        await ctx.followup.send(embed=loaded_embed, view=view, ephemeral=True)

    def _create_embed_from_data(self, embed_data: dict) -> discord.Embed:
        """임베드 객체 생성"""
        embed = discord.Embed(
            title=embed_data.get("title"),
            description=embed_data.get("description"),
            color=embed_data.get("color", 0x3498DB)
        )
        
        for field in embed_data.get("fields", []):
            embed.add_field(
                name=field.get("name"),
                value=field.get("value"),
                inline=field.get("inline", False)
            )
        
        if embed_data.get("author"):
            embed.set_author(name=embed_data["author"])
        
        if embed_data.get("footer"):
            embed.set_footer(text=embed_data["footer"])
        
        if embed_data.get("image"):
            embed.set_image(url=embed_data["image"])
        
        if embed_data.get("thumbnail"):
            embed.set_thumbnail(url=embed_data["thumbnail"])
        
        return embed


class EmbedListView(discord.ui.View):
    """임베드 목록 View"""

    def __init__(self, bot: discord.Bot, user_id: int, embed_names: list[str]):
        super().__init__(timeout=600)
        self.bot = bot
        self.user_id = user_id
        self.embed_names = embed_names

    @discord.ui.button(label="불러오기", style=discord.ButtonStyle.primary)
    async def load_button(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """임베드 불러오기"""
        select = discord.ui.Select(
            placeholder="불러올 임베드를 선택하세요",
            options=[
                discord.SelectOption(label=name, value=name)
                for name in self.embed_names
            ]
        )
        
        async def select_callback(select_interaction: discord.Interaction) -> None:
            selected_name = select.values[0]
            
            if not self.bot.data_manager:
                embed = discord.Embed(
                    description="데이터 관리자가 초기화되지 않았습니다.",
                    color=0xE74C3C
                )
                await select_interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed_data = self.bot.data_manager.get_embed(self.user_id, selected_name)
            
            if embed_data:
                loaded_embed = self._create_embed_from_data(embed_data)
                view = LoadedEmbedView(self.bot, self.user_id, loaded_embed, embed_data, selected_name)
                
                await select_interaction.response.send_message(
                    embed=loaded_embed,
                    view=view,
                    ephemeral=True
                )
        
        select.callback = select_callback
        view = discord.ui.View()
        view.add_item(select)
        
        await interaction.response.send_message(view=view, ephemeral=True)

    @discord.ui.button(label="삭제", style=discord.ButtonStyle.danger)
    async def delete_button(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """임베드 삭제"""
        select = discord.ui.Select(
            placeholder="삭제할 임베드를 선택하세요",
            options=[
                discord.SelectOption(label=name, value=name)
                for name in self.embed_names
            ]
        )
        
        async def select_callback(select_interaction: discord.Interaction) -> None:
            selected_name = select.values[0]
            
            if not self.bot.data_manager:
                return
            
            success = self.bot.data_manager.delete_embed(self.user_id, selected_name)
            
            if success:
                embed = discord.Embed(
                    description=f"'{selected_name}'이 삭제되었습니다.",
                    color=0x2ECC71
                )
            else:
                embed = discord.Embed(
                    description="삭제에 실패했습니다.",
                    color=0xE74C3C
                )
            
            await select_interaction.response.send_message(embed=embed, ephemeral=True)
        
        select.callback = select_callback
        view = discord.ui.View()
        view.add_item(select)
        
        await interaction.response.send_message(view=view, ephemeral=True)

    def _create_embed(self, embed_data: dict) -> discord.Embed:
        """임베드 객체 생성"""
        embed = discord.Embed(
            title=embed_data.get("title"),
            description=embed_data.get("description"),
            color=embed_data.get("color", 0x3498DB)
        )
        
        for field in embed_data.get("fields", []):
            embed.add_field(
                name=field.get("name"),
                value=field.get("value"),
                inline=field.get("inline", False)
            )
        
        return embed


class LoadedEmbedView(discord.ui.View):
    """불러온 임베드 View"""

    def __init__(self, bot: discord.Bot, user_id: int, embed: discord.Embed, embed_data: dict, name: str):
        super().__init__(timeout=600)
        self.bot = bot
        self.user_id = user_id
        self.embed = embed
        self.embed_data = embed_data
        self.name = name

    @discord.ui.button(label="이 채널에 전송", style=discord.ButtonStyle.success)
    async def send_button(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """이 채널에 임베드 전송"""
        try:
            await interaction.channel.send(embed=self.embed)
            embed = discord.Embed(
                description="임베드가 전송되었습니다.",
                color=0x2ECC71
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                description=f"전송 실패: {str(e)[:100]}",
                color=0xE74C3C
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="JSON 내보내기", style=discord.ButtonStyle.secondary)
    async def export_button(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """JSON으로 내보내기"""
        json_str = json.dumps(self.embed_data, indent=2, ensure_ascii=False)
        
        if len(json_str) > 1900:
            await interaction.response.send_message(
                file=discord.File(
                    fp=discord.utils.io.BytesIO(json_str.encode()),
                    filename=f"{self.name}.json"
                ),
                ephemeral=True
            )
        else:
            embed = discord.Embed(
                title=f"'{self.name}' JSON",
                description=f"```json\n{json_str}\n```",
                color=0x3498DB
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


def setup(bot: discord.Bot):
    """명령어 로드"""
    bot.add_cog(ManageCommand(bot))
