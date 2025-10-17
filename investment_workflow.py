import pandas as pd
import os
import sys
import yfinance as yf
import pandas_ta as ta
import io
import configparser
from datetime import datetime
import pytz

# 경로 문제 해결 및 config 임포트
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from index_screener import get_index_tickers
from trading_strategy_analyzer import find_buy_signals
from fundamental_analyzer import get_fundamental_analysis

# 설정 파일 로드
config = configparser.ConfigParser()
config.read(os.path.join(PROJECT_ROOT, 'config.ini'))

def run_investment_workflow():
    """
    최적화된 3단계 투자 분석 워크플로우를 실행합니다.
    """
    # --- 0. 로그 파일 초기화 ---
    try:
        console_log_path = os.path.join(PROJECT_ROOT, 'discord', 'logs', 'console.log')
        with open(console_log_path, 'w', encoding='utf-8') as f:
            f.write(f"--- Workflow run at {datetime.now(pytz.timezone('Asia/Seoul')).strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    except Exception:
        pass # 로그 파일 초기화 실패 시에도 워크플로우는 계속 진행

    # --- 0. 분석 조건 설정 (config.ini에서 로드) ---
    screener_index_name = config.get('Screener', 'index_name')
    if len(sys.argv) > 1 and sys.argv[1] in ["SP500", "NASDAQ100"]:
        screener_index_name = sys.argv[1]
    
    screener_rsi_threshold = config.getint('Screener', 'rsi_threshold')
    screener_use_peg_filter = config.getboolean('Screener', 'use_peg_filter')
    screener_peg_threshold = config.getfloat('Screener', 'peg_threshold')
    analyzer_min_signals_to_find = config.getint('Analyzer', 'min_signals_to_find')
    analyzer_initial_rsi_threshold = config.getint('Analyzer', 'initial_rsi_threshold')
    analyzer_max_rsi_threshold = screener_rsi_threshold
    analyzer_use_strict_filter = config.getboolean('Analyzer', 'use_strict_filter')
    analyzer_use_bollinger_band = config.getboolean('Analyzer', 'use_bollinger_band')
    analyzer_bollinger_band_mode = config.get('Analyzer', 'bollinger_band_mode')
    analyzer_bollinger_band_relaxed_pct = config.getfloat('Analyzer', 'bollinger_band_relaxed_pct')
    analyzer_use_volume_filter = config.getboolean('Analyzer', 'use_volume_filter')
    use_analyst_filter = config.getboolean('Fundamental', 'use_analyst_filter')

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

    # --- 1.5단계: 산업별 평균 Forward P/E 계산 ---
    print("\n--- 1.5단계: 전체 산업별 평균 Forward P/E 계산 시작 ---")
    sector_pes = {}
    for i, ticker in enumerate(all_tickers):
        progress_msg = f"  - 진행: [{i + 1}/{len(all_tickers)}] {ticker} 정보 조회 중..."
        print(progress_msg, end='\r')
        try:
            stock_info = yf.Ticker(ticker).info
            sector = stock_info.get('sector')
            forward_pe = stock_info.get('forwardPE')
            if sector and forward_pe and forward_pe > 0:
                if sector not in sector_pes:
                    sector_pes[sector] = []
                sector_pes[sector].append(forward_pe)
        except Exception:
            continue # 정보 조회 실패 시 건너뛰기

    sector_avg_pe = {}
    for sector, pe_list in sector_pes.items():
        sector_avg_pe[sector] = sum(pe_list) / len(pe_list)
    
    print("\n--- 산업별 평균 P/E 계산 완료 ---")
    # print(sector_avg_pe) # 디버그 필요시 주석 해제

    # --- 2. 저평가 후보 종목 스크리닝 (메모리 기반) ---
    watchlist_data = {}
    print("\n--- 2단계: 저평가 후보 종목 스크리닝 (메모리 기반) ---")
    print(f"[스크리닝 조건] RSI < {screener_rsi_threshold}" + (f" | 0 < PEG < {screener_peg_threshold}" if screener_use_peg_filter else ""))

    for i, (ticker, df) in enumerate(all_ticker_data.items()):
        progress_msg = f"  - 진행: [{i + 1}/{len(all_ticker_data)}] {ticker}"
        print(progress_msg, end='\r')

        if df.empty or 'RSI_14' not in df.columns:
            continue

        latest_rsi = df.iloc[-1]['RSI_14']
        if not (pd.notna(latest_rsi) and latest_rsi < screener_rsi_threshold):
            continue

        # PEG 필터 적용 (필요시)
        if screener_use_peg_filter:
            try:
                stock_info = yf.Ticker(ticker).info
                peg_ratio = stock_info.get('pegRatio')
                if not (peg_ratio is not None and 0 < peg_ratio < screener_peg_threshold):
                    continue # PEG 조건 미충족 시 건너뛰기
            except Exception as e:
                # print(f"\n  - {ticker} PEG 정보 조회 오류: {e}") # 디버그 필요시 주석 해제
                continue # 정보 조회 실패 시 해당 종목은 제외

        # 모든 필터를 통과한 경우에만 추가
        watchlist_data[ticker] = df
    
    print("\n스크리닝 완료!                                  ")

    if not watchlist_data:
        print("\n2단계 스크리닝 결과, 저평가 후보 종목을 찾지 못했습니다.")
        return

    print(f"\n--- 2단계 결과: 최종 관심 종목 리스트 ({len(watchlist_data)}개) ---")
    print(", ".join(watchlist_data.keys()))

    # --- 3. 매수 타이밍 포착 (메모리 기반) ---
    print("\n\n--- 3단계: 매수 타이밍 포착 시작 ---")
    print(f"[추세 조건] {'엄격 모드' if analyzer_use_strict_filter else '완화 모드'}")

    analyzer_rsi_threshold = analyzer_initial_rsi_threshold
    previous_rsi_threshold = 0
    cumulative_signals = set()

    while analyzer_rsi_threshold <= analyzer_max_rsi_threshold:
        print(f"\n- RSI < {analyzer_rsi_threshold} 기준으로 매수 신호 분석 시도...")
        
        eligible_data = {ticker: df for ticker, df in watchlist_data.items() 
                         if not df.empty and 'RSI_14' in df.columns and 
                         df.iloc[-1]['RSI_14'] < analyzer_rsi_threshold and 
                         df.iloc[-1]['RSI_14'] >= previous_rsi_threshold}
        
        if not eligible_data:
            print("  -> 이 기준 범위에 해당하는 분석 대상 종목이 없습니다. 다음 기준으로 넘어갑니다.")
            previous_rsi_threshold = analyzer_rsi_threshold
            analyzer_rsi_threshold += 5
            continue

        print(f"  -> 분석 대상: {len(eligible_data)}개 종목")

        current_signals = find_buy_signals(
            eligible_data,
            rsi_threshold=analyzer_rsi_threshold,
            use_strict_filter=analyzer_use_strict_filter,
            use_bollinger_band=analyzer_use_bollinger_band,
            bollinger_band_mode=analyzer_bollinger_band_mode,
            bollinger_band_relaxed_pct=analyzer_bollinger_band_relaxed_pct,
            use_volume_filter=analyzer_use_volume_filter
        )
        
        if current_signals:
            cumulative_signals.update(current_signals)
            print(f"  -> 신호 발견! (RSI: {analyzer_rsi_threshold}, {len(current_signals)}개 추가, 누적 {len(cumulative_signals)}개)")
        else:
            print("  -> 신호 없음.")
        
        if len(cumulative_signals) >= analyzer_min_signals_to_find:
            print(f"  -> 목표 신호 개수({analyzer_min_signals_to_find}개) 달성. 분석을 종료합니다.")
            break
        
        previous_rsi_threshold = analyzer_rsi_threshold
        analyzer_rsi_threshold += 5

    final_buy_signals = list(cumulative_signals)

    # --- 4. 최종 결과 및 펀더멘탈 필터링 ---
    if not final_buy_signals:
        print(f"\n\n--- 최종 결과: 모든 RSI 기준({analyzer_initial_rsi_threshold}~{analyzer_max_rsi_threshold})에서 매수 신호를 찾지 못했습니다. ---")
        return

    unique_signals = sorted(list(set(final_buy_signals)))
    print(f"\n\n--- 3단계 결과: 기술적 분석 통과 종목 ({len(unique_signals)}개) ---")
    print(", ".join(unique_signals))

    # --- 4단계: 애널리스트 의견 필터링 (옵션) ---
    if use_analyst_filter:
        print("\n--- 4단계: 애널리스트 의견 필터링 시작 (Buy 또는 Strong Buy) ---")
        fundamental_buy_signals = []
        for ticker in unique_signals:
            print(f"  - {ticker} 펀더멘탈 확인 중...", end='\r')
            try:
                stock = yf.Ticker(ticker)
                recommendation = stock.info.get('recommendationKey')
                if recommendation in ['buy', 'strong_buy']:
                    fundamental_buy_signals.append(ticker)
            except Exception:
                continue
        print("\n필터링 완료!")

        if not fundamental_buy_signals:
            print("\n--- 최종 결과: 애널리스트 의견이 Buy/Strong Buy인 종목이 없습니다. ---")
            return
        
        final_signals_to_analyze = fundamental_buy_signals
    else:
        final_signals_to_analyze = unique_signals

    # --- 5. 최종 후보 펀더멘탈 심층 분석 ---
    print(f"\n\n--- 4단계 결과: 최종 후보 종목 ({len(final_signals_to_analyze)}개) ---")
    print(", ".join(final_signals_to_analyze))

    result_filepath = os.path.join(PROJECT_ROOT, "fundamental_analysis_results.txt")
    print(f"\n--- 5단계: 최종 후보 펀더멘탈 심층 분석 (결과 파일: {result_filepath}) ---")
    
    chunk_size = 2
    all_chunks_output = []

    for i in range(0, len(final_signals_to_analyze), chunk_size):
        chunk_tickers = final_signals_to_analyze[i:i+chunk_size]
        chunk_output = []
        
        chunk_output.append(f"--- 펀더멘탈 분석 (Part {i//chunk_size + 1}/{len(final_signals_to_analyze)//chunk_size + (1 if len(final_signals_to_analyze)%chunk_size > 0 else 0)}) ---\n")

        for ticker in chunk_tickers:
            original_stdout = sys.stdout
            temp_output = io.StringIO()
            sys.stdout = temp_output
            try:
                get_fundamental_analysis(ticker, sector_avg_pe)
                sys.stdout.write("-" * 50 + "\n")
            finally:
                sys.stdout = original_stdout
            chunk_output.append(temp_output.getvalue())
        
        all_chunks_output.append("\n".join(chunk_output))

    with open(result_filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(all_chunks_output))

    # 디스코드 요약 메시지를 위한 별도 파일 생성
    summary_filepath = os.path.join(PROJECT_ROOT, "workflow_summary.txt")
    with open(summary_filepath, "w", encoding="utf-8") as f:
        f.write(f"**분석 완료!** 최종 매수 신호 종목 ({len(final_signals_to_analyze)}개)를 찾았습니다.\n")
        f.write(f"티커: {', '.join(final_signals_to_analyze)}\n")
        f.write("상세 리포트를 보려면 `/report` 명령어를 사용하세요.")

    print("분석 완료.")

if __name__ == '__main__':
    run_investment_workflow()