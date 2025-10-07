import yfinance as yf
import pandas_ta as ta
import pandas as pd

def find_buy_signals(tickers, rsi_threshold=30, short_ma=20, mid_ma=50, long_ma=200, use_strict_filter=False, rsi_period=14, bollinger_band_mode='relaxed', bollinger_band_relaxed_pct=1.0, use_volume_filter=True):
    """
    설명된 매수 전략에 따라 매수 신호가 발생한 종목을 찾습니다.
    """
    buy_signals = []
    total_tickers = len(tickers)

    for i, ticker in enumerate(tickers):
        progress_msg = f"  - 2단계 진행: [{i + 1}/{total_tickers}] {ticker}"

        try:
            df = yf.download(ticker, period="250d", auto_adjust=True, progress=False, timeout=10)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)

            if df.empty:
                print(f"{progress_msg} (데이터 없음 -> SKIP)          ", end='\r')
                continue

            # --- 지표 계산 및 직접 할당 (컬럼 이름 문제 해결) ---
            # append=True 대신, 계산 결과를 직접 새 컬럼에 할당합니다.
            df[f'SMA_{short_ma}'] = df.ta.sma(length=short_ma)
            df[f'SMA_{mid_ma}'] = df.ta.sma(length=mid_ma)
            df[f'SMA_{long_ma}'] = df.ta.sma(length=long_ma)
            df[f'RSI_{rsi_period}'] = df.ta.rsi(length=rsi_period)
            df['VOLUME_SMA_20'] = df.ta.sma(close=df['Volume'], length=20)

            bbands = df.ta.bbands(length=20, std=2.0)
            if bbands is not None and not bbands.empty:
                # bbands의 컬럼 이름이 무엇이든, 순서에 기반하여 예측 가능한 이름으로 할당합니다.
                df['BBL_20_2.0'] = bbands.iloc[:, 0]

            # --- 필수 컬럼 확인 --- 
            short_ma_col = f'SMA_{short_ma}'
            mid_ma_col = f'SMA_{mid_ma}'
            long_ma_col = f'SMA_{long_ma}'
            rsi_col = f'RSI_{rsi_period}'
            bb_low_col = 'BBL_20_2.0'
            vol_sma_col = 'VOLUME_SMA_20'

            required_cols = [short_ma_col, mid_ma_col, long_ma_col, rsi_col, bb_low_col, vol_sma_col]
            if not all(col in df.columns for col in required_cols):
                missing_cols = [col for col in required_cols if col not in df.columns]
                print(f"{progress_msg} (지표 계산 불가: {', '.join(missing_cols)} 누락 -> SKIP)          ", end='\r')
                continue

            if len(df) < long_ma:
                print(f"{progress_msg} (데이터 기간 부족 -> SKIP)          ", end='\r')
                continue

            print(f"{progress_msg} (분석 중...)          ", end='\r')

            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]

            # --- 전략 로직 ---
            if use_strict_filter:
                is_uptrend = (last_row[short_ma_col] > last_row[mid_ma_col] > last_row[long_ma_col]) and \
                             (last_row['Close'] > last_row[mid_ma_col])
            else:
                is_uptrend = (last_row['Close'] > last_row[long_ma_col]) and \
                             (last_row[mid_ma_col] > last_row[long_ma_col])

            rsi_crossed_up = last_row[rsi_col] > rsi_threshold and prev_row[rsi_col] < rsi_threshold
            
            if bollinger_band_mode == 'strict':
                touched_bollinger_low = prev_row['Close'] < prev_row[bb_low_col]
            elif bollinger_band_mode == 'relaxed':
                touched_bollinger_low = prev_row['Close'] <= (prev_row[bb_low_col] * (1 + bollinger_band_relaxed_pct / 100))
            else: # 'normal'
                touched_bollinger_low = prev_row['Close'] <= prev_row[bb_low_col]
            
            # 거래량 필터 사용 여부에 따라 최종 조건 분기
            if use_volume_filter:
                volume_spike = last_row['Volume'] > last_row[vol_sma_col] * 1.5
                if is_uptrend and rsi_crossed_up and touched_bollinger_low and volume_spike:
                    buy_signals.append(ticker)
            else:
                if is_uptrend and rsi_crossed_up and touched_bollinger_low:
                    buy_signals.append(ticker)

        except Exception as e:
            error_msg = repr(e).strip()
            print(f"{progress_msg} (오류: {error_msg} -> SKIP)          ", end='\r')
            continue

    return buy_signals

if __name__ == '__main__':
    ticker_list = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META"]
    print("매수 신호 분석 시작...")
    signals = find_buy_signals(ticker_list, rsi_period=14)

    if signals:
        print("\n--- 매수 신호 포착된 종목---")
        for ticker in signals:
            print(f"- {ticker}")
    else:
        print("\n매수 신호가 포착된 종목이 없습니다.")
