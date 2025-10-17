import discord
from discord import app_commands

from config_manager import (
    get_config_display_string, 
    update_config_setting, 
    get_configurable_options,
    get_choices_for_key
)

# --- 자동 완성을 위한 헬퍼 함수 ---
async def section_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """섹션 자동 완성"""
    options = get_configurable_options()
    all_sections = list(options.keys())
    return [
        app_commands.Choice(name=section, value=section)
        for section in all_sections if current.lower() in section.lower()
    ]

async def key_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """키 자동 완성 (선택된 섹션 기반)"""
    selected_section = interaction.namespace.section
    options = get_configurable_options()
    if not selected_section or selected_section not in options:
        return []
    
    all_keys = list(options[selected_section].keys())
    return [
        app_commands.Choice(name=key, value=key)
        for key in all_keys if current.lower() in key.lower()
    ]

async def value_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    """값 자동 완성 (선택된 키 기반)"""
    section = interaction.namespace.section
    key = interaction.namespace.key
    
    if not section or not key:
        return []

    choices = get_choices_for_key(section, key)
    if not choices:
        return []

    return [
        app_commands.Choice(name=choice, value=choice)
        for choice in choices if current.lower() in choice.lower()
    ]

# --- 명령어 셋업 함수 ---
def setup_commands(tree: app_commands.CommandTree, guild: discord.Object, logger):
    """봇에 슬래시 명령어를 추가합니다."""

    @tree.command(name="config_view", description="현재 config.ini 파일의 모든 설정을 확인합니다.", guild=guild)
    async def config_view(interaction: discord.Interaction):
        """현재 설정 값을 보여주는 명령어"""
        await interaction.response.defer(thinking=True, ephemeral=True)
        try:
            config_str = get_config_display_string()
            await interaction.followup.send(f"**현재 설정 (`config.ini`)**\n{config_str}", ephemeral=True)
        except Exception as e:
            logger.error(f"/config_view 명령어 오류: {e}")
            await interaction.followup.send("설정을 불러오는 중 오류가 발생했습니다.", ephemeral=True)

    @tree.command(name="config_set", description="config.ini 파일의 특정 설정을 변경합니다.", guild=guild)
    @app_commands.autocomplete(section=section_autocomplete, key=key_autocomplete, value=value_autocomplete)
    @app_commands.describe(section="변경할 설정의 섹션 (예: Screener)", key="변경할 설정의 키 (예: rsi_threshold)", value="새로운 값")
    async def config_set(interaction: discord.Interaction, section: str, key: str, value: str):
        """설정 값을 변경하는 명령어"""
        await interaction.response.defer(thinking=True, ephemeral=True)
        try:
            success, message = update_config_setting(section, key, value)
            if success:
                await interaction.followup.send(f"✅ 설정 변경 성공: {message}", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ 설정 변경 실패: {message}", ephemeral=True)
        except Exception as e:
            logger.error(f"/config_set 명령어 오류: {e}")
            await interaction.followup.send("설정 변경 중 오류가 발생했습니다.", ephemeral=True)