import os
import subprocess
import sys

# --- 프로젝트 루트 경로 설정 ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- 헬퍼 함수 ---
PYTHON_EXECUTABLE = sys.executable

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

# This function will now be empty as commands are defined directly in bot.py
def setup_commands(tree, guild, logger):
    pass