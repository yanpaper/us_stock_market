import pandas as pd
import os
import sys
import yfinance as yf
import pandas_ta as ta
import io # io 모듈 임포트
from datetime import datetime
import pytz

# 경로 문제 해결을 위해 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from index_screener import get_index_tickers
from trading_strategy_analyzer import find_buy_signals
from fundamental_analyzer import get_fundamental_analysis

def run_investment_workflow(use_cache=True):
    """
    최적화된 3단계 투자 분석 워크플로우를 실행합니다.
    """
    # --- 0. 분석 조건 설정 ---
    screener_index_name = "SP500"
    if len(sys.argv) > 1 and sys.argv[1] in ["SP500", "NASDAQ100"]:
        screener_index_name = sys.argv[1]
    
    screener_rsi_threshold = 60
    analyzer_min_signals_to_find = 5
    analyzer_initial_rsi_threshold = 40
    analyzer_max_rsi_threshold = screener_rsi_threshold
    analyzer_use_strict_filter = False
    analyzer_bollinger_band_mode = 'normal'
    analyzer_bollinger_band_relaxed_pct = 5.0
    analyzer_use_volume_filter = False

    # --- 1. 데이터 사전 로딩 및 지표 계산 ---
    print(f"--- 1단계: {screener_index_name} 데이터 사전 로딩 및 지표 계산 시작 ---")
    all_tickers = get_index_tickers(screener_index_name)
    all_ticker_data = {}
    for i, ticker in enumerate(all_tickers):
        print(f"  - 진행: [{i + 1}/{len(all_tickers)}] {ticker} 데이터 로딩 중...", end='\r')
        try:
            df = yf.download(ticker, period="250d", auto_adjust=True, progress=False, timeout=10)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)

            if df.empty:
                continue
            
            df.ta.sma(length=20, append=True)
            df.ta.sma(length=50, append=True)
            df.ta.sma(length=200, append=True)
            df.ta.rsi(length=14, append=True)
            bbands = df.ta.bbands(length=20, std=2.0)
            if bbands is not None and not bbands.empty:
                df['BBL_20_2.0'] = bbands.iloc[:, 0]
            df['VOLUME_SMA_20'] = df.ta.sma(close=df['Volume'], length=20)
            
            all_ticker_data[ticker] = df
        except Exception as e:
            print(f"\n  - 오류 발생 [{ticker}]: {e}")
            continue
    print("\n--- 데이터 로딩 및 계산 완료 ---")

    # --- 2. 저평가 후보 종목 스크리닝 (메모리 기반) ---
    watchlist_data = {}
    print("\n--- 2단계: 저평가 후보 종목 스크리닝 (메모리 기반) ---")
    debug_count = 0
    for ticker, df in all_ticker_data.items():
        if not df.empty and 'RSI_14' in df.columns:
            latest_rsi = df.iloc[-1]['RSI_14']

            # --- DEBUG PRINT START ---
            if debug_count < 20:
                print(f"  [DEBUG] Ticker: {ticker}, Latest RSI: {latest_rsi}")
                debug_count += 1
            # --- DEBUG PRINT END ---

            if pd.notna(latest_rsi) and latest_rsi < screener_rsi_threshold:
                watchlist_data[ticker] = df

    if not watchlist_data:
        print("\n1단계 스크리닝 결과, 저평가 후보 종목을 찾지 못했습니다.")
        return

    print(f"\n--- 1단계 결과: 최종 관심 종목 리스트 ({len(watchlist_data)}개) ---")
    print(", ".join(watchlist_data.keys()))

    # --- 3. 매수 타이밍 포착 (메모리 기반) ---
    print("\n\n--- 2단계: 매수 타이밍 포착 시작 ---")
    print(f"[추세 조건] {'엄격 모드' if analyzer_use_strict_filter else '완화 모드'}")

    analyzer_rsi_threshold = analyzer_initial_rsi_threshold
    cumulative_signals = set() # 누적 신호를 저장할 set
    final_buy_signals = [] # 최종 결과

    while analyzer_rsi_threshold <= analyzer_max_rsi_threshold:
        print(f"\n- RSI < {analyzer_rsi_threshold} 기준으로 매수 신호 분석 시도...")
        
        eligible_data = {ticker: df for ticker, df in watchlist_data.items() if not df.empty and df.iloc[-1].get('RSI_14', float('inf')) < screener_rsi_threshold} # 스크리너 RSI 기준을 따름
        
        if not eligible_data:
            print("  -> 이 기준에 해당하는 분석 대상 종목이 없습니다.")
            analyzer_rsi_threshold += 5
            continue

        print(f"  -> 분석 대상: {len(eligible_data)}개 종목")

        current_signals = find_buy_signals(
            eligible_data,
            rsi_threshold=analyzer_rsi_threshold,
            use_strict_filter=analyzer_use_strict_filter,
            bollinger_band_mode=analyzer_bollinger_band_mode,
            bollinger_band_relaxed_pct=analyzer_bollinger_band_relaxed_pct,
            use_volume_filter=analyzer_use_volume_filter
        )
        
        if current_signals:
            cumulative_signals.update(current_signals) # 찾은 신호 누적
            print(f"  -> 신호 발견! (RSI: {analyzer_rsi_threshold}, {len(current_signals)}개 추가, 누적 {len(cumulative_signals)}개)")
        else:
            print("  -> 신호 없음.")
        
        if len(cumulative_signals) >= analyzer_min_signals_to_find:
            print(f"  -> 목표 신호 개수({analyzer_min_signals_to_find}개) 달성. 분석을 종료합니다.")
            final_buy_signals = list(cumulative_signals) # 최종 결과에 할당
            break
        
        analyzer_rsi_threshold += 5

    # 루프가 끝까지 돌았지만 목표 개수를 채우지 못했을 경우
    # final_buy_signals는 항상 cumulative_signals의 최종 내용을 담도록 합니다.
    final_buy_signals = list(cumulative_signals)

    # --- 4. 최종 결과 및 펀더멘탈 분석 ---
    if not final_buy_signals:
        print(f"\n\n--- 최종 결과: 모든 RSI 기준({analyzer_initial_rsi_threshold}~{analyzer_max_rsi_threshold})에서 매수 신호를 찾지 못했습니다. ---")
        return

    unique_signals = sorted(list(set(final_buy_signals)))
    print(f"\n\n--- 최종 결과: 지금 매수 신호가 포착된 종목 ({len(unique_signals)}개) ---")
    print(", ".join(unique_signals))

    result_filepath = os.path.join(PROJECT_ROOT, "fundamental_analysis_results.txt")
    print(f"\n--- 3단계: 최종 후보 펀더멘탈 심층 분석 (결과 파일: {result_filepath}) ---")
    
    # 결과를 2개 종목씩 묶어서 파일에 저장
    chunk_size = 2
    all_chunks_output = []
    DELIMITER = "\n--- END_OF_CHUNK ---\n"

    for i in range(0, len(unique_signals), chunk_size):
        chunk_tickers = unique_signals[i:i+chunk_size]
        chunk_output_parts = []
        
        # 각 종목에 대해 펀더멘탈 분석 수행
        for ticker in chunk_tickers:
            # 표준 출력을 임시 StringIO 객체로 리디렉션
            original_stdout = sys.stdout
            temp_output = io.StringIO()
            sys.stdout = temp_output
            try:
                get_fundamental_analysis(ticker)
                sys.stdout.write("-" * 50 + "\n") # StringIO 객체에 직접 write
            finally:
                sys.stdout = original_stdout
            chunk_output_parts.append(temp_output.getvalue())
        
        all_chunks_output.append("\n".join(chunk_output_parts))
        if i + chunk_size < len(unique_signals):
            all_chunks_output.append(DELIMITER) # 다음 청크와의 구분자 추가

    with open(result_filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(all_chunks_output))

    print("분석 완료.")

if __name__ == '__main__':
    run_investment_workflow(use_cache=False) # 캐시 기능은 현재 아키텍처에서 불필요