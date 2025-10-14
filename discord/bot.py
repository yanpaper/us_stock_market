import discord
import os
import subprocess
import json
import logging
from discord import app_commands

# --- 설정 파일 로드 ---
def load_config():
    # 스크립트의 현재 위치를 기준으로 config.json의 절대 경로를 만듭니다.
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

config = load_config()
TOKEN = config['bot_token']
GUILD_ID = config['guild_id']

# --- 로깅 설정 ---
# Critical 로그만 discord/logs/critical.log 파일에 저장
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

# --- 명령어 정의 ---
# subprocess 실행 경로를 프로젝트 루트 디렉토리로 설정
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import asyncio

# ... (기존 임포트 생략) ...

# --- 명령어 정의 ---
# ... (중략) ...

import sys

PYTHON_EXECUTABLE = sys.executable

# ... (기존 임포트 생략) ...

# --- 명령어 정의 ---
# ... (중략) ...

def run_analysis_sync(ticker: str) -> str:
    """동기적으로 분석 스크립트를 실행하고 결과를 반환하는 헬퍼 함수"""
    script_path = os.path.join(PROJECT_ROOT, 'combined_analyzer.py')
    result = subprocess.run(
        [PYTHON_EXECUTABLE, script_path, ticker],
        capture_output=True, text=True, check=True, timeout=120, cwd=PROJECT_ROOT
    )
    return result.stdout

def run_workflow_sync(index_value: str):
    """동기적으로 워크플로우 스크립트를 실행하는 헬퍼 함수"""
    script_path = os.path.join(PROJECT_ROOT, 'investment_workflow.py')
    subprocess.run([PYTHON_EXECUTABLE, script_path, index_value], cwd=PROJECT_ROOT, check=True, timeout=900) # 15분 타임아웃

@client.tree.command()
@app_commands.describe(ticker='분석할 주식 티커 (예: AAPL)')
async def stock(interaction: discord.Interaction, ticker: str):
    """특정 티커의 종합 분석(기술적+펀더멘탈)을 수행합니다."""
    await interaction.response.defer(thinking=True)
    try:
        # 동기 함수를 별도 스레드에서 실행하여 봇의 응답을 유지합니다.
        output = await asyncio.to_thread(run_analysis_sync, ticker)
        
        if len(output) > 1980:
            output = output[:1980] + "... (내용이 너무 길어 잘렸습니다)"
        await interaction.followup.send(f"```\n{output}\n```")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        error_message = e.stderr or str(e)
        logger.critical(f"/stock 명령어 오류 ({ticker}): {error_message}")
        await interaction.followup.send(f"'{ticker}' 분석 중 오류가 발생했습니다. 관리자가 로그를 확인해야 합니다.")

def run_workflow_sync(index_value: str):
    """동기적으로 워크플로우 스크립트를 실행하는 헬퍼 함수"""
    script_path = os.path.join(PROJECT_ROOT, 'investment_workflow.py')
    # Popen 대신 run을 사용하고, 작업이 끝날 때까지 기다립니다.
    subprocess.run([PYTHON_EXECUTABLE, script_path, index_value], cwd=PROJECT_ROOT, check=True, timeout=900) # 15분 타임아웃

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
        await interaction.followup.send(f"{index.name} 지수에 대한 전체 투자 분석 워크플로우를 시작합니다. 최대 30분까지 소요될 수 있으며, 완료되면 이곳에 결과를 게시합니다.")
        
        # 동기 함수를 별도 스레드에서 실행
        await asyncio.to_thread(run_workflow_sync, index.value)

        # 결과 파일을 읽어서 디스코드에 전송
        result_filepath = os.path.join(PROJECT_ROOT, "fundamental_analysis_results.txt")
        if os.path.exists(result_filepath):
            with open(result_filepath, "r", encoding="utf-8") as f:
                full_output = f.read()
            
            # investment_workflow.py에서 정의한 구분자를 사용하여 메시지 분할
            DELIMITER = "\n--- END_OF_CHUNK ---\n"
            chunks = full_output.split(DELIMITER)
            chunks = [chunk.strip() for chunk in chunks if chunk.strip()] # 빈 청크 제거
            total_chunks = len(chunks)

            for i, chunk in enumerate(chunks):
                header = f"**워크플로우 완료!** (Part {i+1}/{total_chunks})\n" if i == 0 else f"(Part {i+1}/{total_chunks})\n"
                message_content = f"{header}```\n{chunk}\n```"
                
                # 디스코드 메시지 길이 제한(2000자) 확인
                if len(message_content) > 2000:
                    message_content = message_content[:1990] + "... (내용이 너무 길어 잘렸습니다)\n```"

                # 첫 메시지는 followup.send로, 이후 메시지는 interaction.channel.send로 보냅니다.
                if i == 0:
                    await interaction.followup.send(message_content)
                else:
                    await interaction.channel.send(message_content)

            os.remove(result_filepath) # 결과 전송 후 파일 삭제
        else:
            await interaction.followup.send("워크플로우는 완료되었으나, 분석 결과 파일이 생성되지 않았습니다.")

    except Exception as e:
        error_message = e.stderr or str(e) if hasattr(e, 'stderr') else str(e)
        logger.critical(f"/workflow 명령어 오류 ({index.name}): {error_message}")
        await interaction.followup.send(f"워크플로우 실행 중 오류가 발생했습니다. 관리자가 로그를 확인해야 합니다.")

# --- 봇 실행 ---
if TOKEN == "YOUR_DISCORD_BOT_TOKEN" or GUILD_ID == 0:
    print("오류: discord/config.json 파일에 봇 토큰과 서버 ID를 올바르게 입력해주세요.")
else:
    client.run(TOKEN, log_handler=handler, log_level=logging.CRITICAL)