# 주식 분석 디스코드 봇 (Stock Analysis Discord Bot)

이 프로젝트는 `yfinance` 라이브러리를 기반으로 미국 주식 시장(S&P 500, NASDAQ 100)의 종목을 분석하고, 그 결과를 디스코드 봇을 통해 쉽게 확인할 수 있도록 만든 자동화 분석 시스템입니다.

## 주요 기능

-   **중앙화된 설정 관리 (`config.ini`):** 모든 분석 전략과 관련된 옵션(RSI 임계값, 이동평균선 기간, 필터 사용 여부 등)을 `config.ini` 파일 하나에서 쉽게 제어할 수 있습니다.
-   **민감 정보 분리 (`discord/secrets.json`):** 디스코드 봇 토큰, 서버 ID 등 민감한 정보는 `discord/secrets.json` 파일에 별도로 보관하며, 이 파일은 `.gitignore`에 의해 Git 저장소에 포함되지 않아 안전합니다.
-   **자동 종목 스크리닝 및 매수 신호 분석:** S&P 500 또는 NASDAQ 100 지수 전체를 대상으로, 기술적 분석을 통해 '관심 종목'을 발굴하고, 복합적인 기술적 지표를 통해 '매수 타이밍'을 포착합니다.
-   **펀더멘탈 필터링 (옵션):** 기술적 분석을 통과한 종목들 중에서 애널리스트 의견이 'Buy' 또는 'Strong Buy'인 종목만 최종 후보로 선정할 수 있습니다. (`config.ini`에서 `use_analyst_filter`로 제어)
-   **개별 종목 종합 분석:** 특정 티커 하나에 대한 상세 기술적 지표와 펀더멘탈 분석 결과, 그리고 간단한 해석 및 포지션 가이드를 즉시 조회할 수 있습니다.
-   **디스코드 연동:** 위 모든 기능을 디스코드의 슬래시(`/`) 명령어를 통해 간편하게 실행하고 결과를 확인할 수 있습니다.

## 설치 필요 라이브러리 (Required Libraries)

이 프로젝트를 실행하기 위해 다음 파이썬 라이브러리들이 필요합니다. 터미널에서 아래 명령어를 사용하여 한 번에 설치할 수 있습니다.

```bash
pip install yfinance pandas pandas-ta lxml pytz requests discord.py
```

## 설치 및 설정

1.  **프로젝트 클론:**
    ```bash
    git clone [프로젝트_레포지토리_URL]
    cd stock_discord
    ```
2.  **파이썬 의존성 설치:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Discord 봇 설정:**
    *   `discord/secrets.json` 파일을 생성하고 다음 형식으로 봇 토큰과 길드 ID를 입력합니다.
        ```json
        {
            "bot_token": "YOUR_DISCORD_BOT_TOKEN",
            "guild_id": YOUR_GUILD_ID,
            "webhook_url": "YOUR_WEBHOOK_URL_OPTIONAL"
        }
        ```
        *   `YOUR_DISCORD_BOT_TOKEN`: Discord 개발자 포털에서 발급받은 봇 토큰.
        *   `YOUR_GUILD_ID`: 봇을 추가할 Discord 서버(길드)의 ID.
        *   `YOUR_WEBHOOK_URL_OPTIONAL`: (선택 사항) 웹훅 URL.
    *   `config.ini` 파일을 열어 분석 전략에 필요한 설정값들을 조정합니다. (예: RSI 임계값, 필터 사용 여부 등)

## 실행 방법

### 1. Discord 봇 실행 (운영용)

Discord 봇을 실행하여 슬래시 명령어를 통해 분석 기능을 사용합니다.

```bash
python discord/bot.py
```

### 2. 터미널에서 전체 투자 워크플로우 실행 (테스트/수동 분석용)

Discord 봇을 통하지 않고 터미널에서 직접 전체 투자 워크플로우를 실행할 수 있습니다. 모든 분석 조건은 `config.ini` 파일에서 수정합니다.

```bash
# S&P 500 지수 분석 (config.ini의 index_name 설정 사용)
python investment_workflow.py

# NASDAQ 100 지수 분석 (명령줄 인자로 오버라이드)
python investment_workflow.py NASDAQ100
```

### 3. 터미널에서 개별 종목 종합 분석 실행 (테스트/수동 분석용)

특정 주식 티커에 대한 기술적 및 펀더멘탈 종합 분석을 즉시 실행합니다.

```bash
# AAPL 티커 분석
python combined_analyzer.py AAPL
```

### 4. Git 업데이트 푸시

프로젝트 변경 사항을 Git 저장소에 커밋하고 푸시합니다.

```bash
./push_updates.sh
```

## Discord 봇 사용법

봇이 실행 중일 때, Discord 서버에서 다음 슬래시 명령어를 사용할 수 있습니다.

*   `/stock <ticker>`: 특정 티커(예: `AAPL`)에 대한 종합 분석(기술적 + 펀더멘탈) 결과를 즉시 제공합니다.
*   `/workflow <index>`: 선택한 시장 지수(예: `S&P 500`, `NASDAQ 100`)에 대한 전체 투자 분석 워크플로우를 시작합니다. 분석 완료 후 요약 결과를 게시하며, 상세 리포트는 `/report` 명령어로 확인할 수 있습니다.
*   `/report`: 가장 최근에 실행된 워크플로우의 상세 펀더멘탈 분석 리포트를 확인합니다.

## 파일 구조 및 역할

이 프로젝트는 다음과 같은 주요 파일과 디렉토리로 구성됩니다.

*   **`config.ini`**: 모든 분석 전략의 설정값을 관리하는 중앙 설정 파일입니다. **(사용자 설정 영역)**
*   **`requirements.txt`**: 프로젝트에 필요한 파이썬 라이브러리 목록을 정의합니다.
*   **`.gitignore`**: Git 버전 관리에서 제외할 파일 및 폴더를 지정합니다.
*   **`push_updates.sh`**: Git 변경 사항을 스테이징, 커밋, 푸시하는 쉘 스크립트입니다.

### 파이썬 스크립트

*   **`investment_workflow.py`**: `config.ini`의 설정을 바탕으로 '종목 발굴'부터 '매수 시점 포착', '펀더멘탈 필터링 및 분석'까지의 전체 과정을 자동으로 실행하는 메인 워크플로우 스크립트입니다.
*   **`index_screener.py`**: 지정된 지수(S&P 500 또는 NASDAQ 100)에서 RSI 및 선택적으로 PEG 비율을 기반으로 잠재적으로 저평가된 '관심 종목'을 발굴합니다.
*   **`trading_strategy_analyzer.py`**: 미리 계산된 데이터프레임에 대해 이동 평균, RSI, 볼린저 밴드, 거래량 필터 등을 사용하여 매수 신호를 식별합니다. `investment_workflow.py`에서 호출됩니다.
*   **`combined_analyzer.py`**: 주어진 주식 티커에 대해 기술적 분석(SMA, RSI, 볼린저 밴드)과 펀더멘탈 분석을 결합하여 포괄적인 분석을 수행합니다. Discord 봇의 `/stock` 명령어를 통해 실행됩니다.
*   **`fundamental_analyzer.py`**: `yfinance`와 웹 스크래핑을 사용하여 주식 티커에 대한 펀더멘탈 및 애널리스트 분석을 제공합니다. `combined_analyzer.py` 및 `investment_workflow.py`에서 호출됩니다.

### `discord/` 디렉토리

*   **`discord/bot.py`**: Discord 봇의 메인 로직을 포함합니다. 슬래시 명령어를 처리하고 다른 분석 스크립트를 실행하여 결과를 Discord 채널에 게시합니다.
*   **`discord/secrets.json`**: Discord 봇 토큰, 길드 ID 등 민감한 정보를 저장하는 파일입니다. **(Git에 포함되지 않음)**
