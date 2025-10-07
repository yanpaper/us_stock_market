# US Stock Market Analysis Toolkit

This repository contains a set of Python scripts designed to analyze the US stock market (S&P 500 and NASDAQ 100) and discover investment opportunities. The workflow is divided into two main stages: screening for potential stocks and analyzing the precise timing for buys.

---

# 미국 주식 시장 분석 툴킷

이 리포지토리는 미국 주식 시장(S&P 500 및 NASDAQ 100)을 분석하고 투자 기회를 발견하기 위해 설계된 파이썬 스크립트 모음입니다. 전체 워크플로우는 잠재적인 종목을 발굴하는 '스크리닝' 단계와 정확한 매수 시점을 분석하는 '타이밍 분석' 단계로 나뉩니다.

---

## Features / 주요 기능

1.  **Automated 2-Step Workflow (`investment_workflow.py`):**
    *   **Step 1 (Screening):** Automatically fetches the latest list of S&P 500 or NASDAQ 100 stocks and filters them based on value and momentum indicators (PEG Ratio, RSI) to create a watchlist.
    *   **Step 2 (Timing Analysis):** Analyzes the stocks from the watchlist to find precise buy signals based on a complex technical strategy (Moving Averages, RSI, Bollinger Bands, Volume).

2.  **Ad-hoc Single Stock Analysis (`single_ticker_analyzer.py`):**
    *   Provides a detailed technical analysis report for any single stock ticker entered by the user.

3.  **Configurable Strategies:**
    *   Most parameters, such as RSI thresholds, moving average periods, and strategy modes (strict/relaxed), are easily configurable within the scripts.

4.  **Smart Caching:**
    *   The screening results are cached daily to speed up subsequent runs and minimize redundant data fetching.

---

## Installation / 설치

Clone the repository and install the required Python libraries.

리포지토리를 클론하고, 필요한 파이썬 라이브러리를 설치합니다.

```bash
# Clone the repository
git clone https://github.com/yanpaper/us_stock_market.git
cd us_stock_market

# Install required libraries
pip install -r requirements.txt
```

*Note: A `requirements.txt` file will be created shortly to manage dependencies.* 
*(참고: 의존성 관리를 위해 `requirements.txt` 파일이 곧 생성될 예정입니다.)*

---

## How to Use / 사용법

### 1. Automated Workflow / 자동 워크플로우 실행

This is the primary way to use the toolkit. It runs the full screening and analysis process.

이것이 이 툴킷을 사용하는 가장 주된 방법입니다. 전체 스크리닝 및 분석 프로세스를 실행합니다.

```bash
python investment_workflow.py
```

- You can configure all analysis conditions inside the `investment_workflow.py` file under the `# --- 0. 분석 조건 설정 ---` section.
- 모든 분석 조건은 `investment_workflow.py` 파일 상단의 `# --- 0. 분석 조건 설정 ---` 섹션에서 직접 수정할 수 있습니다.

### 2. Single Ticker Analysis / 개별 종목 분석

To get a quick technical report for a specific stock.

특정 종목에 대한 기술적 분석 리포트를 빠르게 확인하고 싶을 때 사용합니다.

```bash
# Run with a command-line argument
python single_ticker_analyzer.py AAPL

# Or run without an argument to be prompted for a ticker
python single_ticker_analyzer.py
```

---

## File Structure / 파일 구조

- **`investment_workflow.py`**: The main runner that executes the entire 2-step analysis process. **(이 파일을 실행하세요)**
- **`index_screener.py`**: A module that screens all stocks in a given index (S&P 500 or NASDAQ 100) to find undervalued candidates.
- **`trading_strategy_analyzer.py`**: A module that analyzes a list of tickers to find specific buy signals based on a technical strategy.
- **`single_ticker_analyzer.py`**: A standalone script for analyzing a single stock.
- **`stock_analysis_functions_summary.md`**: Detailed documentation for developers (Korean).
- **`.gitignore`**: Specifies files to be ignored by Git (e.g., cache files).
