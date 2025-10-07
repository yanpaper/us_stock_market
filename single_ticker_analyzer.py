import yfinance as yf
import pandas_ta as ta
import pandas as pd
import sys # sys 모듈 임포트

def analyze_single_ticker(ticker, short_ma=20, mid_ma=50, long_ma=200, rsi_period=14):
    """
    특정 티커에 대한 기술적 분석 지표를 계산하고 출력합니다.

    Args:
        ticker (str): 분석할 주식 티커 (예: "AAPL").
        short_ma (int): 단기 이동평균선 기간. 기본값은 20입니다.
        mid_ma (int): 중기 이동평균선 기간. 기본값은 50입니다.
        long_ma (int): 장기 이동평균선 기간. 기본값은 200입니다.
        rsi_period (int): RSI 계산 기간. 기본값은 14입니다.

    Returns:
        dict: 계산된 최신 지표 값들을 담은 딕셔너리.
              데이터를 가져오거나 계산에 실패하면 None을 반환합니다.
    """
    print(f"\n--- {ticker} 기술적 분석 시작 --- ")
    try:
        # 가장 긴 이평선 계산을 위해 데이터 다운로드 기간을 250일로 늘림
        df = yf.download(ticker, period="250d", auto_adjust=True, progress=False, timeout=10)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        if df.empty:
            print(f"'{ticker}'에 대한 데이터를 가져올 수 없습니다.")
            return None

        # pandas_ta를 사용하여 기술적 지표 동적 계산
        df[f'SMA_{short_ma}'] = df.ta.sma(length=short_ma)
        df[f'SMA_{mid_ma}'] = df.ta.sma(length=mid_ma)
        df[f'SMA_{long_ma}'] = df.ta.sma(length=long_ma)
        df[f'RSI_{rsi_period}'] = df.ta.rsi(length=rsi_period)
        
        bbands = df.ta.bbands(length=20, std=2.0)
        if bbands is not None and not bbands.empty:
            df['BBL_20_2.0'] = bbands.iloc[:, 0] # Lower Bollinger Band
            df['BBM_20_2.0'] = bbands.iloc[:, 1] # Middle Bollinger Band (SMA)
            df['BBU_20_2.0'] = bbands.iloc[:, 2] # Upper Bollinger Band
        else:
            df['BBL_20_2.0'] = pd.NA
            df['BBM_20_2.0'] = pd.NA
            df['BBU_20_2.0'] = pd.NA

        df['VOLUME_SMA_20'] = df.ta.sma(close=df['Volume'], length=20)

        # 가장 긴 이평선을 계산할 만큼 데이터가 충분한지 확인
        if len(df) < long_ma:
            print(f"'{ticker}'에 대한 데이터 기간이 부족합니다 (최소 {long_ma}일 필요). ")
            return None

        last_row = df.iloc[-1]

        # 결과 딕셔너리 생성
        results = {
            "Ticker": ticker,
            "Date": last_row.name.strftime('%Y-%m-%d'),
            "Close": last_row['Close'],
            f"SMA_{short_ma}": last_row[f'SMA_{short_ma}'],
            f"SMA_{mid_ma}": last_row[f'SMA_{mid_ma}'],
            f"SMA_{long_ma}": last_row[f'SMA_{long_ma}'],
            f"RSI_{rsi_period}": last_row[f'RSI_{rsi_period}'],
            "Bollinger_Lower": last_row['BBL_20_2.0'],
            "Bollinger_Middle": last_row['BBM_20_2.0'],
            "Bollinger_Upper": last_row['BBU_20_2.0'],
            "Volume": last_row['Volume'],
            "Volume_SMA_20": last_row['VOLUME_SMA_20']
        }
        
        print("\n--- 최신 기술적 지표 ---")
        for key, value in results.items():
            if isinstance(value, (float, int)) and not pd.isna(value):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")

        # --- 간단 해석 ---
        interpretation = []
        current_price = results['Close']
        current_rsi = results[f'RSI_{rsi_period}']
        sma_short = results[f'SMA_{short_ma}']
        sma_mid = results[f'SMA_{mid_ma}']
        sma_long = results[f'SMA_{long_ma}']
        bb_lower = results['Bollinger_Lower']
        bb_upper = results['Bollinger_Upper']

        # 추세 해석
        if pd.notna(sma_short) and pd.notna(sma_mid) and pd.notna(sma_long):
            if sma_short > sma_mid and sma_mid > sma_long and current_price > sma_short:
                interpretation.append("강력한 상승 추세 (정배열)")
            elif current_price > sma_long and sma_mid > sma_long:
                interpretation.append("상승 추세 (완화된 조건)")
            elif sma_short < sma_mid and sma_mid < sma_long and current_price < sma_short:
                interpretation.append("강력한 하락 추세 (역배열)")
            elif current_price < sma_long and sma_mid < sma_long:
                interpretation.append("하락 추세 (완화된 조건)")
            else:
                interpretation.append("혼조세 또는 횡보 추세")
        else:
            interpretation.append("이동평균선 데이터 부족으로 추세 판단 불가")

        # RSI 해석
        if pd.notna(current_rsi):
            if current_rsi > 70:
                interpretation.append(f"RSI ({current_rsi:.2f}): 과매수 구간 (조정 가능성)")
            elif current_rsi < 30:
                interpretation.append(f"RSI ({current_rsi:.2f}): 과매도 구간 (반등 가능성)")
            else:
                interpretation.append(f"RSI ({current_rsi:.2f}): 중립 구간")
        else:
            interpretation.append("RSI 데이터 부족")

        # 볼린저 밴드 해석
        if pd.notna(bb_lower) and pd.notna(bb_upper):
            if current_price > bb_upper:
                interpretation.append(f"볼린저 밴드: 상단 돌파 (과열 또는 강한 상승 모멘텀)")
            elif current_price < bb_lower:
                interpretation.append(f"볼린저 밴드: 하단 이탈 (과매도 또는 강한 하락 모멘텀)")
            elif current_price > results['Bollinger_Middle']:
                interpretation.append(f"볼린저 밴드: 중간선 위 (상승 압력)")
            else:
                interpretation.append(f"볼린저 밴드: 중간선 아래 (하락 압력)")
        else:
            interpretation.append("볼린저 밴드 데이터 부족")

        print("\n--- 간단 해석 ---")
        for item in interpretation:
            print(f"- {item}")
        
        return results

    except Exception as e:
        print(f"'{ticker}' 분석 중 오류 발생: {e}")
        return None

if __name__ == '__main__':
    if len(sys.argv) > 1:
        ticker_to_analyze = sys.argv[1].upper() # 명령줄 인자로 티커 받기
    else:
        ticker_to_analyze = input("분석할 티커를 입력하세요 (예: AAPL): ").upper() # 사용자 입력 받기

    if ticker_to_analyze:
        analyze_single_ticker(ticker_to_analyze)
    else:
        print("티커가 입력되지 않아 분석을 시작할 수 없습니다.")
