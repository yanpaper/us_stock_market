# 주식 분석 스크립트 요약 (Stock Analysis Scripts Summary)

이 문서는 현재 폴더에 있는 파이썬 주식 분석 스크립트들의 기능과 사용법을 요약합니다.

---

## 설치 필요 라이브러리 (Required Libraries)

아래 스크립트들을 실행하기 위해 다음 라이브러리들이 필요합니다. 터미널에서 아래 명령어를 사용하여 한 번에 설치할 수 있습니다.

```bash
pip install yfinance pandas pandas_ta lxml pytz discord.py requests
```

---

## 파일 구성 및 역할

총 5개의 파이썬 파일과 2개의 설정 파일이 있으며, 각 파일은 다음과 같은 역할을 수행합니다.

1.  **`config.ini`**: 모든 분석 전략의 설정값을 관리하는 중앙 설정 파일입니다.
2.  **`discord/secrets.json`**: 디스코드 봇 토큰, 서버 ID, 웹훅 URL과 같이 민감한 정보를 저장합니다. (.gitignore에 포함되어 커밋되지 않음)
3.  **`investment_workflow.py`**: `config.ini`의 설정을 바탕으로 전체 분석 워크플로우를 실행하는 메인 스크립트입니다.
4.  **`index_screener.py`**: 지정된 지수(SP500 또는 NASDAQ100)에서 '관심 종목'을 발굴합니다.
5.  **`trading_strategy_analyzer.py`**: 선정된 '관심 종목'의 구체적인 '매수 시점'을 포착합니다.
6.  **`combined_analyzer.py`**: 특정 티커 하나에 대한 종합 분석(기술적+펀더멘탈)을 제공합니다.
7.  **`fundamental_analyzer.py`**: `combined_analyzer.py`와 `investment_workflow.py`에 의해 호출되어 펀더멘탈 분석을 수행합니다.
8.  **`discord/`**: 디스코드 봇 관련 파일들을 포함하는 폴더.

---

## 1. `config.ini` (중앙 설정)

모든 분석 스크립트에서 사용되는 설정값들을 섹션별로 정의합니다. 사용자는 이 파일만 수정하여 모든 분석 전략을 쉽게 제어할 수 있습니다.

## 2. `investment_workflow.py` (워크플로우 실행)

`config.ini`의 설정을 바탕으로 '종목 발굴'부터 '매수 시점 포착', '펀더멘탈 필터링 및 분석'까지의 전체 과정을 자동으로 실행합니다.

- **사용법:**
  - 터미널에서 **`python investment_workflow.py [SP500 또는 NASDAQ100]`** 명령으로 실행합니다.
  - 모든 세부 조건은 **`config.ini`** 파일에서 수정합니다.

## 3. `discord/bot.py` (디스코드 봇)

디스코드 슬래시 명령어를 통해 분석 스크립트들을 실행하고 결과를 채널에 게시합니다.

- **`/stock <ticker>`**: `combined_analyzer.py`를 실행하여 특정 티커의 종합 분석 결과를 제공합니다.
- **`/workflow <index>`**: `investment_workflow.py`를 실행하여 선택한 지수에 대한 전체 분석 워크플로우를 시작하고, 최종 펀더멘탈 분석 결과를 채널에 게시합니다.

(각 분석 모듈의 상세 설명은 이전과 동일하므로 생략합니다.)
