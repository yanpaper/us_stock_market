import discord
import os
import subprocess
import json
import logging
import asyncio
import sys
from discord import app_commands

# --- 설정 파일 로드 ---
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'secrets.json')
    with open(config_path, 'r') as f:
        return json.load(f)

config = load_config()
TOKEN = config['bot_token']
GUILD_ID = config['guild_id']
WEBHOOK_URL = config['webhook_url']

# --- 로깅 설정 ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_dir = os.path.join(PROJECT_ROOT, 'discord', 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logger = logging.getLogger('discord')
logger.setLevel(logging.CRITICAL)
handler = logging.FileHandler(filename=os.path.join(log_dir, 'critical.log'), encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# --- 봇 설정 ---
MY_GUILD = discord.Object(id=GUILD_ID)
PYTHON_EXECUTABLE = sys.executable

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

intents = discord.Intents.default()
client = MyClient(intents=intents)

# --- 이벤트 핸들러 ---
@client.event
async def on_ready():
    print(f'로그인: {client.user} (ID: {client.user.id})')
    print('------')

# --- 헬퍼 함수 ---
def run_analysis_sync(ticker: str) -> str:
    script_path = os.path.join(PROJECT_ROOT, 'combined_analyzer.py')
    result = subprocess.run(
        [PYTHON_EXECUTABLE, script_path, ticker],
        capture_output=True, text=True, check=True, timeout=120, cwd=PROJECT_ROOT
    )
    return result.stdout

def run_workflow_sync(index_value: str):
    script_path = os.path.join(PROJECT_ROOT, 'investment_workflow.py')
    subprocess.run([PYTHON_EXECUTABLE, script_path, index_value], cwd=PROJECT_ROOT, check=True, timeout=900)

# --- 명령어 정의 ---
@client.tree.command()
@app_commands.describe(ticker='분석할 주식 티커 (예: AAPL)')
async def stock(interaction: discord.Interaction, ticker: str):
    """특정 티커의 종합 분석(기술적+펀더멘탈)을 수행합니다."""
    await interaction.response.defer(thinking=True)
    try:
        output = await asyncio.to_thread(run_analysis_sync, ticker)
        if len(output) > 1980:
            output = output[:1980] + "... (내용이 너무 길어 잘렸습니다)"
        await interaction.followup.send(f"```\n{output}\n```")
    except Exception as e:
        error_message = e.stderr if hasattr(e, 'stderr') else str(e)
        logger.critical(f"/stock 명령어 오류 ({ticker}): {error_message}")
        await interaction.followup.send(f"'{ticker}' 분석 중 오류가 발생했습니다. 관리자가 로그를 확인해야 합니다.")

@client.tree.command()
@app_commands.describe(index='분석할 시장 지수를 선택합니다.')
@app_commands.choices(index=[
    discord.app_commands.Choice(name='S&P 500', value='SP500'),
    discord.app_commands.Choice(name='NASDAQ 100', value='NASDAQ100'),
])
async def workflow(interaction: discord.Interaction, index: discord.app_commands.Choice[str]):
    """선택한 시장 지수에 대한 전체 투자 분석 워크플로우를 시작합니다."""
    await interaction.response.defer(thinking=True)
    try:
        await interaction.followup.send(f"{index.name} 지수에 대한 전체 투자 분석 워크플로우를 시작합니다. 최대 15분까지 소요될 수 있으며, 완료되면 요약 결과를 게시합니다.")
        
        await asyncio.to_thread(run_workflow_sync, index.value)

        await asyncio.sleep(1) # 파일 시스템 I/O 지연을 위한 1초 대기

        summary_filepath = os.path.join(PROJECT_ROOT, "workflow_summary.txt")
        if os.path.exists(summary_filepath):
            with open(summary_filepath, "r", encoding="utf-8") as f:
                summary_output = f.read()
            await interaction.followup.send(summary_output)
            os.remove(summary_filepath)
        else:
            await interaction.followup.send("워크플로우는 완료되었으나, 요약 파일이 생성되지 않았습니다.")

    except Exception as e:
        error_message = e.stderr if hasattr(e, 'stderr') else str(e)
        logger.critical(f"/workflow 명령어 오류 ({index.name}): {error_message}")
        await interaction.followup.send(f"워크플로우 실행 중 오류가 발생했습니다. 관리자가 로그를 확인해야 합니다.")

@client.tree.command()
async def report(interaction: discord.Interaction):
    """가장 최근에 실행된 워크플로우의 상세 분석 리포트를 확인합니다."""
    await interaction.response.defer(thinking=True)
    try:
        result_filepath = os.path.join(PROJECT_ROOT, "fundamental_analysis_results.txt")
        if os.path.exists(result_filepath):
            with open(result_filepath, "r", encoding="utf-8") as f:
                full_output = f.read()
            
            # "--- 펀더멘탈 분석"을 기준으로 메시지 분할
            chunks = full_output.split("--- 펀더멘탈 분석")
            chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

            if not chunks:
                await interaction.followup.send("상세 리포트 파일은 있으나 내용이 비어있습니다.")
            else:
                for i, chunk in enumerate(chunks):
                    message_content = f"--- 펀더멘탈 분석{chunk}"
                    if len(message_content) > 1980:
                        message_content = message_content[:1980] + "... (내용이 너무 길어 잘렸습니다)"
                    
                    if i == 0:
                        await interaction.followup.send(f"**상세 리포트**\n```\n{message_content}\n```")
                    else:
                        await interaction.channel.send(f"```\n{message_content}\n```")

            os.remove(result_filepath)
        else:
            await interaction.followup.send("표시할 상세 리포트가 없습니다. 먼저 `/workflow`를 실행해주세요.")

    except Exception as e:
        error_message = e.stderr if hasattr(e, 'stderr') else str(e)
        logger.critical(f"/report 명령어 오류: {error_message}")
        await interaction.followup.send("리포트 생성 중 오류가 발생했습니다. 관리자가 로그를 확인해야 합니다.")



# --- 봇 실행 ---
if TOKEN == "YOUR_DISCORD_BOT_TOKEN" or GUILD_ID == 0:
    print("오류: discord/config.json 파일에 봇 토큰과 서버 ID를 올바르게 입력해주세요.")
else:
    client.run(TOKEN, log_handler=handler, log_level=logging.CRITICAL)
