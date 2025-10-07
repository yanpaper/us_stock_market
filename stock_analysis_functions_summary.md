# 주식 분석 스크립트 요약 (Stock Analysis Scripts Summary)

이 문서는 현재 폴더에 있는 파이썬 주식 분석 스크립트들의 기능과 사용법을 요약합니다.

---

## 설치 필요 라이브러리 (Required Libraries)

아래 스크립트들을 실행하기 위해 다음 라이브러리들이 필요합니다. 터미널에서 아래 명령어를 사용하여 한 번에 설치할 수 있습니다.

```bash
pip install yfinance pandas pandas_ta lxml pytz
```

---

## 파일 구성 및 역할

총 4개의 파이썬 파일이 있으며, 각 파일은 다음과 같은 역할을 수행합니다.

1.  **`index_screener.py`**: 지정된 지수(SP500 또는 NASDAQ100)에서 '관심 종목'을 발굴합니다. **(What to buy?)**
2.  **`trading_strategy_analyzer.py`**: 선정된 '관심 종목'의 구체적인 '매수 시점'을 포착합니다. **(When to buy?)**
3.  **`investment_workflow.py`**: 위 1, 2번 과정을 자동으로 연결하고 모든 설정을 제어하는 최종 실행 파일입니다. **(Main Runner)**
4.  **`single_ticker_analyzer.py`**: 특정 티커 하나에 대한 기술적 분석을 제공합니다. **(Ad-hoc Analysis)**

---

## 1. `index_screener.py` (종목 발굴)

지정된 지수(SP500 또는 NASDAQ100) 전체 종목을 대상으로, 간단한 가치/모멘텀 기준을 통해 잠재적인 투자 후보군을 발굴(스크리닝)하는 역할을 합니다.

### `get_index_tickers(index_name="SP500")`

- **기능:** Wikipedia에서 지정된 지수(SP500 또는 NASDAQ100)의 종목 티커 리스트를 가져옵니다. 403 Forbidden 오류를 피하기 위해 User-Agent 헤더를 추가합니다.
- **인자:**
  - `index_name` (str): 가져올 지수의 이름 (`"SP500"` 또는 `"NASDAQ100"`). (기본값: `"SP500"`)
- **반환값:** 지정된 지수의 종목 티커(`str`)들의 리스트(`list`)

### `find_undervalued_stocks(rsi_threshold=50, peg_threshold=1.0, use_peg_filter=True, rsi_period=14, index_name="SP500")`

- **기능:** 지정된 지수의 모든 종목 중에서 설정된 조건에 맞는 '저평가 후보' 종목을 찾아냅니다.
- **인자:**
  - `rsi_threshold` (int): RSI 기준값. 이 값 미만인 종목을 찾습니다. (기본값: `50`)
  - `peg_threshold` (float): PEG Ratio 기준값. `use_peg_filter`가 `True`일 때 사용됩니다. (기본값: `1.0`)
  - `use_peg_filter` (bool): PEG Ratio 필터를 사용할지 여부. (기본값: `True`)
  - `rsi_period` (int): RSI 계산 기간. (기본값: `14`)
  - `index_name` (str): 분석할 지수의 이름 (`"SP500"` 또는 `"NASDAQ100"`). (기본값: `"SP500"`)
- **반환값:** 조건에 맞는 종목의 티커, RSI, PEG 값을 담은 딕셔너리(`dict`)의 리스트(`list`)

---

## 2. `trading_strategy_analyzer.py` (매수 시점 포착)

미리 선정된 관심 종목들을 대상으로, 복합적인 기술적 지표를 통해 구체적인 매수 '시점'을 포착하는 역할을 합니다.

### `find_buy_signals(tickers, rsi_threshold=30, short_ma=20, mid_ma=50, long_ma=200, use_strict_filter=False, rsi_period=14, bollinger_band_mode='relaxed', bollinger_band_relaxed_pct=1.0, use_volume_filter=True)`

- **기능:** 주어진 종목 리스트에서 복합적인 기술적 매수 신호가 발생한 종목을 찾아냅니다. 모든 조건은 파라미터를 통해 제어할 수 있습니다.
- **핵심 전략:**
  - **추세 필터 (`use_strict_filter`):**
    - `True` (엄격 모드): 단기 > 중기 > 장기 이평선 정배열 및 주가가 중기/장기 이평선 위에 있을 것.
    - `False` (완화 모드, 기본값): 주가가 장기 이평선 위에 있고, 중기 이평선이 장기 이평선 위에 있을 것.
  - **RSI 신호:** RSI가 과매도 구간(`rsi_threshold` 미만)에 진입했다가 상향 돌파할 것.
  - **볼린저 밴드 필터 (`bollinger_band_mode`):**
    - `strict`: 직전 과매도 상태에서 주가가 볼린저 밴드 하단 `BBL` 미만일 것.
    - `normal`: 직전 과매도 상태에서 주가가 볼린저 밴드 하단 `BBL` 이하일 것.
    - `relaxed` (기본값): 직전 과매도 상태에서 주가가 `BBL`의 `(1 + bollinger_band_relaxed_pct / 100)` 범위 내에 있을 것.
  - **거래량 필터 (`use_volume_filter`):**
    - `True` (기본값): RSI 상향 돌파 시, 거래량이 20일 평균 거래량의 1.5배 이상일 것.
    - `False`: 거래량 조건 무시.
- **인자:**
  - `tickers` (list): 분석할 주식 티커들의 리스트.
  - `rsi_threshold` (int): RSI 과매도 기준값. (기본값: `30`)
  - `short_ma`, `mid_ma`, `long_ma` (int): 단/중/장기 이평선 기간. (기본값: `20`, `50`, `200`)
  - `use_strict_filter` (bool): 엄격한 추세 필터 사용 여부. (기본값: `False`)
  - `rsi_period` (int): RSI 계산 기간. (기본값: `14`)
  - `bollinger_band_mode` (str): 볼린저 밴드 필터 모드 (`'strict'`, `'normal'`, `'relaxed'`). (기본값: `'relaxed'`)
  - `bollinger_band_relaxed_pct` (float): `relaxed` 모드에서 볼린저 밴드 하단 근접 허용 비율(%). (기본값: `1.0`)
  - `use_volume_filter` (bool): 거래량 필터 사용 여부. (기본값: `True`)
- **반환값:** 매수 신호가 포착된 종목의 티커(`str`)들의 리스트(`list`)

---

## 3. `investment_workflow.py` (워크플로우 실행)

전체 투자 분석 워크플로우를 실행하고 모든 세부 조건을 설정하는 메인 스크립트입니다.

### `run_investment_workflow(use_cache=True)`

- **기능:** '종목 발굴'부터 '매수 시점 포착'까지의 전체 과정을 자동으로 실행합니다.
- **주요 기능 및 로직:**
  1.  **분석 조건 설정:** 파일 상단에 모든 스크리너 및 분석기 조건을 변수로 정의하여 쉽게 변경 가능합니다.
  2.  **자동 캐시 관리:** 오늘 날짜 이전의 낡은 캐시 파일(`watchlist_*.csv`)을 자동으로 삭제합니다. 오늘 날짜와 조건이 일치하는 캐시가 있으면 1단계 스크리닝을 건너뛰고 재활용합니다. 캐시 파일명에 선택된 지수 이름이 포함되어 지수별로 캐시가 분리 관리되며, 파일명에 사용되는 지수 이름은 공백과 `&` 문자가 제거되고 대문자로 변환됩니다.
  3.  **1단계 (스크리닝):** `index_screener.py`의 `find_undervalued_stocks()`를 호출하여 지정된 지수에서 저평가 후보군(관심 종목)을 발굴하고, 결과를 `.csv` 파일로 저장합니다.
  4.  **2단계 (신호 분석):** `trading_strategy_analyzer.py`의 `find_buy_signals()`를 호출합니다. 만약 설정된 초기 RSI 기준(`analyzer_initial_rsi_threshold`)에서 신호가 없으면, 신호가 나올 때까지 RSI 기준을 5씩 자동으로 높여가며(최대 `analyzer_max_rsi_threshold`까지) 재시도합니다. **최소 `analyzer_min_signals_to_find` 개수 이상의 신호를 찾거나 최대 RSI 기준에 도달할 때까지 반복합니다.**
- **인자:**
  - `use_cache` (bool): 캐시 기능을 사용할지 여부. `True`이면 오늘자 캐시 파일을 재활용합니다. (기본값: `True`)
- **사용법:**
  - 터미널에서 **`python investment_workflow.py`** 명령어 하나만 실행하면 모든 분석이 자동으로 진행됩니다.
  - 모든 세부 조건은 `investment_workflow.py` 파일 상단의 **`# --- 0. 분석 조건 설정 ---`** 섹션에서 변수 값을 수정하여 쉽게 제어할 수 있습니다.

---

## 4. `single_ticker_analyzer.py` (개별 종목 분석)

사용자가 입력한 특정 티커 하나에 대한 기술적 분석 지표를 계산하고 출력합니다.

### `analyze_single_ticker(ticker, short_ma=20, mid_ma=50, long_ma=200, rsi_period=14)`

- **기능:** 특정 주식 티커에 대한 최신 기술적 분석 지표(이동평균선, RSI, 볼린저 밴드, 거래량)를 계산하고 보기 좋게 출력하며, **각 지표에 대한 간단한 해석을 함께 제공합니다.**
- **인자:**
  - `ticker` (str): 분석할 주식의 티커 (예: `"AAPL"`).
  - `short_ma`, `mid_ma`, `long_ma` (int): 단/중/장기 이동평균선 기간. (기본값: `20`, `50`, `200`)
  - `rsi_period` (int): RSI 계산 기간. (기본값: `14`)
- **반환값:** 계산된 최신 지표 값들을 담은 딕셔너리(`dict`). 데이터를 가져오거나 계산에 실패하면 `None`을 반환합니다.
- **사용법:**
  - 터미널에서 **`python single_ticker_analyzer.py [티커]`** (예: `python single_ticker_analyzer.py AAPL`) 명령으로 실행합니다.
  - 티커를 입력하지 않으면, 스크립트가 실행 중 사용자에게 티커를 입력하라는 프롬프트를 띄웁니다.