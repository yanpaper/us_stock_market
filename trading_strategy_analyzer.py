import yfinance as yf
import pandas_ta as ta
import pandas as pd
import time

def find_buy_signals(ticker_dataframes: dict, rsi_threshold=30, short_ma=20, mid_ma=50, long_ma=200, use_strict_filter=False, rsi_period=14, bollinger_band_mode='relaxed', bollinger_band_relaxed_pct=1.0, use_volume_filter=True):
    """
    미리 계산된 데이터프레임에 대해 매수 신호 분석을 수행합니다.
    """
    buy_signals = []
    for ticker, df in ticker_dataframes.items():
        try:
            # 데이터프레임이 비어있거나 기간이 짧으면 건너뛰기
            if df.empty or len(df) < long_ma:
                continue

            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]

            # 컬럼 이름을 동적으로 생성
            short_ma_col = f'SMA_{short_ma}'
            mid_ma_col = f'SMA_{mid_ma}'
            long_ma_col = f'SMA_{long_ma}'
            rsi_col = f'RSI_{rsi_period}'
            bb_low_col = 'BBL_20_2.0'
            vol_sma_col = 'VOLUME_SMA_20'
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
            
            volume_spike = False # 기본값 초기화
            # 거래량 필터 사용 여부에 따라 최종 조건 분기
            if use_volume_filter:
                volume_spike = last_row['Volume'] > last_row[vol_sma_col] * 1.5
                if is_uptrend and rsi_crossed_up and touched_bollinger_low and volume_spike:
                    buy_signals.append(ticker)
            else: # 'normal'
                if is_uptrend and rsi_crossed_up and touched_bollinger_low:
                    buy_signals.append(ticker)

            # --- [DEBUG FOR ORLY] --- (주석 처리된 디버그 블록)
            # if ticker == 'ORLY':
            #     print(f"\n--- [DEBUG FOR ORLY] ---")
            #     print(f"  - is_uptrend: {is_uptrend}")
            #     print(f"    - Close: {last_row['Close']:.2f}, SMA_{long_ma}: {last_row[long_ma_col]:.2f} (Price > Long MA: {last_row['Close'] > last_row[long_ma_col]})")
            #     print(f"    - SMA_{mid_ma}: {last_row[mid_ma_col]:.2f}, SMA_{long_ma}: {last_row[long_ma_col]:.2f} (Mid MA > Long MA: {last_row[mid_ma_col] > last_row[long_ma_col]})")
            #     print(f"  - rsi_crossed_up: {rsi_crossed_up}")
            #     print(f"    - last_rsi: {last_row[rsi_col]:.2f}, prev_rsi: {prev_row[rsi_col]:.2f}, threshold: {rsi_threshold}")
            #     print(f"  - touched_bollinger_low: {touched_bollinger_low}")
            #     print(f"    - prev_close: {prev_row['Close']:.2f}, prev_bbl: {prev_row[bb_low_col]:.2f}")
            #     print(f"  - volume_spike: {volume_spike} (필터 {'활성화' if use_volume_filter else '비활성화'}) ")
            #     if use_volume_filter:
            #         print(f"    - last_volume: {last_row['Volume']}, avg_volume: {last_row[vol_sma_col] * 1.5}")
            #     print(f"------------------------")

        except Exception as e:
            error_msg = repr(e).strip()
            print(f"\n  - 오류 [{ticker}]: {error_msg} -> SKIP")
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
