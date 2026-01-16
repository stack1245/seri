"""임베드 생성 명령어"""
from __future__ import annotations
import json
import logging
from typing import Optional
import discord
from discord.ext import commands

from utils.constants import EMBED_COLORS, MAX_EMBED_FIELDS

logger = logging.getLogger(__name__)


class EmbedCreateModal(discord.ui.Modal):
    """임베드 생성 모달"""

    def __init__(self, callback):
        super().__init__(title="임베드 생성", timeout=600)
        self.callback_func = callback
        
        # 제목
        self.add_item(
            discord.ui.InputText(
                label="제목 (선택)",
                placeholder="임베드의 제목을 입력하세요",
                required=False,
                max_length=256
            )
        )
        
        # 설명
        self.add_item(
            discord.ui.InputText(
                label="설명",
                placeholder="임베드의 주요 내용을 입력하세요",
                required=True,
                style=discord.InputTextStyle.long,
                max_length=4096
            )
        )
        
        # 색상
        self.add_item(
            discord.ui.InputText(
                label="색상 (선택)",
                placeholder="예: RED, BLUE, GREEN (또는 16진수: 0xFF0000)",
                required=False,
                max_length=10
            )
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """모달 제출 시 호출"""
        await self.callback_func(interaction, self.children)


class CreateEmbedButton(discord.ui.View):
    """임베드 생성 버튼 View"""

    def __init__(self, callback):
        super().__init__(timeout=None)
        self.callback_func = callback

    @discord.ui.button(label="제목 추가", style=discord.ButtonStyle.secondary)
    async def add_title_button(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """제목 추가 버튼"""
        modal = discord.ui.Modal(title="제목 설정")
        modal.add_item(
            discord.ui.InputText(
                label="제목",
                placeholder="임베드 제목",
                required=True,
                max_length=256
            )
        )
        
        async def modal_callback(modal_interaction: discord.Interaction) -> None:
            await self.callback_func(modal_interaction, {"action": "set_title", "value": modal.children[0].value})
        
        modal.callback = modal_callback
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="필드 추가", style=discord.ButtonStyle.secondary)
    async def add_field_button(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """필드 추가 버튼"""
        modal = discord.ui.Modal(title="필드 추가")
        modal.add_item(
            discord.ui.InputText(
                label="필드 이름",
                placeholder="필드의 이름",
                required=True,
                max_length=256
            )
        )
        modal.add_item(
            discord.ui.InputText(
                label="필드 값",
                placeholder="필드의 내용",
                required=True,
                style=discord.InputTextStyle.long,
                max_length=1024
            )
        )
        modal.add_item(
            discord.ui.InputText(
                label="인라인 (yes/no)",
                placeholder="yes 또는 no",
                required=False,
                max_length=3
            )
        )
        
        async def modal_callback(modal_interaction: discord.Interaction) -> None:
            inline = modal.children[2].value.lower() == "yes" if modal.children[2].value else False
            await self.callback_func(modal_interaction, {
                "action": "add_field",
                "name": modal.children[0].value,
                "value": modal.children[1].value,
                "inline": inline
            })
        
        modal.callback = modal_callback
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="색상 변경", style=discord.ButtonStyle.secondary)
    async def change_color_button(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """색상 변경 버튼"""
        colors_list = ", ".join(EMBED_COLORS.keys())
        
        modal = discord.ui.Modal(title="색상 설정")
        modal.add_item(
            discord.ui.InputText(
                label="색상",
                placeholder=f"선택: {colors_list[:50]}...",
                required=True,
                max_length=10
            )
        )
        
        async def modal_callback(modal_interaction: discord.Interaction) -> None:
            await self.callback_func(modal_interaction, {"action": "set_color", "value": modal.children[0].value})
        
        modal.callback = modal_callback
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="미리보기", style=discord.ButtonStyle.primary)
    async def preview_button(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """미리보기 버튼"""
        await self.callback_func(interaction, {"action": "preview"})

    @discord.ui.button(label="저장", style=discord.ButtonStyle.success)
    async def save_button(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """저장 버튼"""
        await self.callback_func(interaction, {"action": "save"})

    @discord.ui.button(label="완료", style=discord.ButtonStyle.success)
    async def done_button(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        """완료 버튼"""
        await self.callback_func(interaction, {"action": "done"})


class CreateCommand(commands.Cog):
    """임베드 생성 명령어"""

    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.user_embeds: dict[int, dict] = {}

    @discord.slash_command(name="create", description="새로운 임베드를 생성합니다")
    async def create_embed(self, ctx: discord.ApplicationContext) -> None:
        """임베드 생성 명령어"""
        # 사용자의 임베드 초기화
        self.user_embeds[ctx.user.id] = {
            "title": None,
            "description": None,
            "color": 0x3498DB,
            "fields": [],
            "author": None,
            "footer": None,
            "image": None,
            "thumbnail": None
        }

        # 첫 번째 모달 표시
        modal = EmbedCreateModal(self._handle_initial_modal)
        await ctx.response.send_modal(modal)

    async def _handle_initial_modal(self, interaction: discord.Interaction, items) -> None:
        """초기 모달 처리"""
        user_id = interaction.user.id
        
        if user_id not in self.user_embeds:
            await interaction.response.defer()
            return
        
        embed_data = self.user_embeds[user_id]
        
        # 모달 입력값 처리
        title = items[0].value if items[0].value else None
        description = items[1].value
        color_str = items[2].value if len(items) > 2 and items[2].value else "BLUE"
        
        embed_data["title"] = title
        embed_data["description"] = description
        
        # 색상 파싱
        if color_str.upper() in EMBED_COLORS:
            embed_data["color"] = EMBED_COLORS[color_str.upper()]
        else:
            try:
                embed_data["color"] = int(color_str.replace("0x", ""), 16)
            except ValueError:
                embed_data["color"] = 0x3498DB

        # 빌더 View 표시
        view = CreateEmbedButton(self._handle_builder_action)
        
        embed = discord.Embed(
            title="임베드 빌더",
            description="아래 버튼을 사용하여 임베드를 커스터마이징하세요.",
            color=0x3498DB
        )
        embed.add_field(name="현재 설정", value=self._get_embed_summary(user_id), inline=False)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def _handle_builder_action(self, interaction: discord.Interaction, action_data: dict) -> None:
        """빌더 액션 처리"""
        user_id = interaction.user.id
        
        if user_id not in self.user_embeds:
            await interaction.response.defer()
            return
        
        embed_data = self.user_embeds[user_id]
        action = action_data.get("action")

        if action == "set_title":
            embed_data["title"] = action_data.get("value")
            await interaction.response.defer()

        elif action == "add_field":
            if len(embed_data["fields"]) >= 25:
                embed = discord.Embed(
                    description="최대 25개의 필드만 추가할 수 있습니다.",
                    color=0xE74C3C
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            field = {
                "name": action_data.get("name"),
                "value": action_data.get("value"),
                "inline": action_data.get("inline", False)
            }
            embed_data["fields"].append(field)
            await interaction.response.defer()

        elif action == "set_color":
            color_str = action_data.get("value", "").upper()
            if color_str in EMBED_COLORS:
                embed_data["color"] = EMBED_COLORS[color_str]
            else:
                try:
                    embed_data["color"] = int(color_str.replace("0x", ""), 16)
                except ValueError:
                    await interaction.response.send_message(
                        "유효하지 않은 색상입니다.",
                        ephemeral=True
                    )
                    return
            await interaction.response.defer()

        elif action == "preview":
            preview_embed = self._create_embed(embed_data)
            await interaction.response.send_message(embed=preview_embed, ephemeral=True)
            return

        elif action == "save":
            modal = discord.ui.Modal(title="임베드 저장")
            modal.add_item(
                discord.ui.InputText(
                    label="임베드 이름",
                    placeholder="저장할 임베드의 이름을 입력하세요",
                    required=True,
                    max_length=50
                )
            )
            
            async def save_modal_callback(save_interaction: discord.Interaction) -> None:
                embed_name = modal.children[0].value
                
                if self.bot.data_manager:
                    self.bot.data_manager.save_embed(user_id, embed_name, embed_data)
                    
                    embed = discord.Embed(
                        description=f"'{embed_name}'으로 저장되었습니다.",
                        color=0x2ECC71
                    )
                    await save_interaction.response.send_message(embed=embed, ephemeral=True)
            
            modal.callback = save_modal_callback
            await interaction.response.send_modal(modal)
            return

        elif action == "done":
            # 최종 임베드 표시
            final_embed = self._create_embed(embed_data)
            
            send_view = SendEmbedView(final_embed, embed_data)
            embed = discord.Embed(
                description="임베드 생성이 완료되었습니다. 아래에서 임베드를 전송하거나 JSON으로 내보낼 수 있습니다.",
                color=0x2ECC71
            )
            await interaction.response.send_message(embed=embed, view=send_view, ephemeral=True)
            
            if user_id in self.user_embeds:
                del self.user_embeds[user_id]
            return

        # 상태 업데이트 메시지
        view = CreateEmbedButton(self._handle_builder_action)
        embed = discord.Embed(
            title="임베드 빌더",
            description="아래 버튼을 사용하여 임베드를 계속 커스터마이징하세요.",
            color=0x3498DB
        )
        embed.add_field(name="현재 설정", value=self._get_embed_summary(user_id), inline=False)
        
        # 이전 메시지 수정 (defer 후 불가능하므로 새 메시지)
        if action != "preview" and action != "save" and action != "done":
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

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
        
        if embed_data.get("author"):
            embed.set_author(name=embed_data["author"])
        
        if embed_data.get("footer"):
            embed.set_footer(text=embed_data["footer"])
        
        if embed_data.get("image"):
            embed.set_image(url=embed_data["image"])
        
        if embed_data.get("thumbnail"):
            embed.set_thumbnail(url=embed_data["thumbnail"])
        
        return embed

    def _get_embed_summary(self, user_id: int) -> str:
        """임베드 요약 정보"""
        if user_id not in self.user_embeds:
            return "임베드 정보 없음"
        
        data = self.user_embeds[user_id]
        summary = ""
        
        if data.get("title"):
            summary += f"제목: {data['title']}\n"
        if data.get("description"):
            summary += f"설명: {data['description'][:50]}...\n"
        
        field_count = len(data.get("fields", []))
        if field_count > 0:
            summary += f"필드: {field_count}개\n"
        
        color = data.get("color", 0x3498DB)
        summary += f"색상: #{color:06X}"
        
        return summary if summary else "기본 설정 상태"


class SendEmbedView(discord.ui.View):
    """임베드 전송 View"""

    def __init__(self, embed: discord.Embed, embed_data: dict):
        super().__init__(timeout=600)
        self.embed = embed
        self.embed_data = embed_data

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
        
        # 너무 길면 파일로 전송
        if len(json_str) > 1900:
            await interaction.response.send_message(
                file=discord.File(
                    fp=discord.utils.io.BytesIO(json_str.encode()),
                    filename="embed.json"
                ),
                ephemeral=True
            )
        else:
            embed = discord.Embed(
                title="임베드 JSON",
                description=f"```json\n{json_str}\n```",
                color=0x3498DB
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


def setup(bot: discord.Bot):
    """명령어 로드"""
    bot.add_cog(CreateCommand(bot))
