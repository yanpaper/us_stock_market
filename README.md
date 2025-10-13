# 주식 분석 디스코드 봇 (Stock Analysis Discord Bot)

이 프로젝트는 `yfinance` 라이브러리를 기반으로 미국 주식 시장(S&P 500, NASDAQ 100)의 종목을 분석하고, 그 결과를 디스코드 봇을 통해 쉽게 확인할 수 있도록 만든 자동화 분석 시스템입니다.

## 주요 기능

-   **자동 종목 스크리닝**: S&P 500 또는 NASDAQ 100 지수 전체를 대상으로, 설정된 조건(PEG, RSI)에 맞는 '관심 종목'을 발굴합니다.
-   **자동 매수 신호 분석**: 발굴된 '관심 종목' 중에서 복합적인 기술적 지표(이동평균선, RSI, 볼린저밴드, 거래량)를 통해 구체적인 '매수 타이밍'을 포착합니다.
-   **개별 종목 종합 분석**: 특정 티커 하나에 대한 상세 기술적 지표와 펀더멘탈 분석 결과, 그리고 간단한 해석 및 포지션 가이드를 즉시 조회할 수 있습니다.
-   **디스코드 연동**: 위 모든 기능을 디스코드의 슬래시(`/`) 명령어를 통해 간편하게 실행하고 결과를 확인할 수 있습니다.
-   **스마트 캐싱 및 재시도**: 워크플로우 실행 시 데이터 로딩 및 분석 과정에서 캐싱과 재시도 로직을 통해 효율성과 안정성을 높였습니다.

## 설치 및 설정

### 1. 소스 코드 다운로드

이 프로젝트의 모든 파일을 다운로드합니다.

### 2. 필요 라이브러리 설치

터미널에서 프로젝트 최상위 폴더로 이동한 뒤, 아래 명령어를 실행하여 프로젝트 실행에 필요한 모든 파이썬 라이브러리를 설치합니다.

```bash
pip install yfinance pandas pandas_ta lxml pytz discord.py requests
```

### 3. 디스코드 봇 생성 및 설정

1.  **봇 생성 및 토큰 발급**:
    - [Discord 개발자 포털](https://discord.com/developers/applications)에 접속하여 새 애플리케이션을 생성합니다.
    - `Bot` 탭으로 이동하여 봇을 추가하고, **[Reset Token]** 버튼을 눌러 나타나는 **봇 토큰(Bot Token)**을 복사합니다. (이 토큰은 절대로 외부에 노출되면 안 됩니다.)

2.  **봇 서버 초대**:
    - `OAuth2 > URL Generator` 탭으로 이동합니다.
    - **SCOPES**에서 `bot`과 `applications.commands`를 체크합니다.
    - **BOT PERMISSIONS**에서 `Send Messages`, `Read Message History` 등 필요한 권한을 부여합니다. (간단하게 `Administrator`를 선택해도 무방합니다.)
    - 생성된 URL을 복사하여 웹 브라우저로 접속한 뒤, 봇을 추가하고 싶은 당신의 디스코드 서버를 선택하여 초대합니다.

3.  **서버 ID 확인**:
    - 디스코드 앱에서 서버 아이콘을 마우스 오른쪽 버튼으로 클릭하고 **[서버 ID 복사]**를 선택합니다.
    - (만약 메뉴가 보이지 않는다면, `디스코드 설정 > 고급`에서 **개발자 모드**를 활성화하세요.)

4.  **설정 파일 수정**:
    - `discord/config.json` 파일을 엽니다.
    - `bot_token`의 값으로 1번에서 복사한 **실제 봇 토큰**을 붙여넣습니다.
    - `guild_id`의 값으로 3번에서 복사한 **실제 서버 ID**를 붙여넣습니다.

    ```json
    {
        "bot_token": "YOUR_DISCORD_BOT_TOKEN",
        "guild_id": 123456789012345678
    }
    ```

## 실행 방법

### 1. 디스코드 봇 실행 (운영용)

봇을 24시간 안정적으로 운영하려면 터미널에서 프로젝트 최상위 폴더로 이동한 뒤 아래 명령어를 사용하세요.

```bash
cd /home/gemini/project/stock_discord # 프로젝트 최상위 폴더로 이동
nohup python -u discord/bot.py > discord/logs/console.log 2>&1 &
```
-   이 명령어를 실행하면 터미널을 닫아도 봇이 계속 실행됩니다.
-   모든 일반 로그는 `discord/logs/console.log`에, 심각한 오류는 `discord/logs/critical.log`에 저장됩니다.
-   봇 종료: `ps aux | grep discord/bot.py`로 PID를 찾은 후 `kill [PID]`

### 2. 부팅 시 자동 실행 (Crontab)

리눅스 서버 재부팅 시 봇을 자동으로 실행하려면 `crontab -e` 명령어로 편집기를 열고 아래 내용을 추가하세요.

```bash
@reboot mkdir -p {project dir}/discord/logs && (cd {project dir} && /usr/bin/python3 -u discord/bot.py) > {project dir}/discord/logs/cron.log 2>&1
```
-   **중요**: `{project dir}` 부분은 실제 프로젝트 경로로 반드시 변경해야 합니다.

### 3. 터미널에서 직접 워크플로우 실행 (테스트/수동 분석용)

디스코드 봇을 통하지 않고 터미널에서 직접 전체 워크플로우를 실행할 수 있습니다.

```bash
# S&P 500 지수 분석 (기본값)
python investment_workflow.py

# NASDAQ 100 지수 분석
python investment_workflow.py NASDAQ100
```
-   모든 분석 조건은 `investment_workflow.py` 파일 상단의 `# --- 0. 분석 조건 설정 ---` 섹션에서 직접 수정할 수 있습니다.
-   결과는 `fundamental_analysis_results.txt` 파일에 저장됩니다.

### 4. 터미널에서 개별 종목 종합 분석 실행 (테스트/수동 분석용)

특정 종목 하나에 대한 기술적 및 펀더멘탈 분석을 즉시 실행할 수 있습니다.

```bash
# 명령줄 인자로 티커 제공
python combined_analyzer.py AAPL

# 인자 없이 실행하여 프롬프트에서 티커 입력
python combined_analyzer.py
```

## 디스코드 봇 사용법

디스코드 채널의 채팅창에 슬래시(`/`)를 입력하여 아래 명령어들을 사용할 수 있습니다.

### `/stock`
특정 종목의 최신 기술적 지표와 펀더멘탈 분석 결과, 그리고 간단한 해석 및 포지션 가이드를 조회합니다.
-   **사용 예시**: `/stock ticker:NVDA`

### `/workflow`
선택한 시장 지수(S&P 500 또는 NASDAQ 100)에 대한 전체 투자 분석 워크플로우를 백그라운드에서 실행합니다.
-   **사용 예시**: `/workflow index:S&P 500` 또는 `/workflow index:NASDAQ 100`
-   **주의**: 이 명령어의 상세 결과는 봇이 실행되고 있는 **디스코드 채널에 직접 게시**됩니다. (최대 30분 소요)

## 파일 구조

-   **`index_screener.py`**: 지정된 지수(SP500 또는 NASDAQ100)에서 '관심 종목'을 발굴합니다.
-   **`trading_strategy_analyzer.py`**: 선정된 '관심 종목'의 구체적인 '매수 시점'을 포착합니다.
-   **`investment_workflow.py`**: 위 두 스크립트를 연결하고 모든 설정을 제어하는 최종 실행 파일입니다.
-   **`combined_analyzer.py`**: 특정 티커 하나에 대한 종합 분석(기술적+펀더멘탈)을 제공합니다.
-   **`fundamental_analyzer.py`**: `combined_analyzer.py`에 의해 호출되어 펀더멘탈 분석을 수행합니다.
-   **`discord/`**: 디스코드 봇 관련 파일들을 포함하는 폴더.
    -   `discord/bot.py`: 디스코드 봇의 메인 로직.
    -   `discord/config.json`: 봇 토큰과 서버 ID를 저장하는 설정 파일.
    -   `discord/logs/`: 봇 실행 로그가 저장되는 폴더.
-   **`stock_analysis_functions_summary.md`**: 개발자를 위한 상세한 함수별 문서 (한국어).
-   **`requirements.txt`**: 프로젝트 의존성 라이브러리 목록.
-   **`.gitignore`**: Git이 추적하지 않을 파일 및 폴더 목록 (예: 캐시 파일, 설정 파일).
