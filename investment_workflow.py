import pandas as pd
import os
from datetime import datetime
import pytz
from index_screener import find_undervalued_stocks
from trading_strategy_analyzer import find_buy_signals

def run_investment_workflow(use_cache=True):
    """
    스마트 캐시, 최적화, 자동 재시도 기능이 포함된 2단계 투자 분석 워크플로우를 실행합니다.
    
    Args:
        use_cache (bool): 캐시 기능을 사용할지 여부. True이면 오늘자 캐시 파일을 재활용합니다.
    """
    # --- 0. 분석 조건 설정 ---
    #screener_index_name = "NASDAQ100" # "SP500" 또는 "NASDAQ100" 선택
    screener_index_name = "SP500" # "SP500" 또는 "NASDAQ100" 선택
    screener_rsi_period = 14
    screener_rsi_threshold = 60
    screener_use_peg_filter = False
    screener_peg_threshold = 2.0
    
    analyzer_rsi_period = 14
    analyzer_initial_rsi_threshold = 40
    analyzer_max_rsi_threshold = screener_rsi_threshold
    analyzer_min_signals_to_find = 5 # 최소한 찾아야 할 매수 신호 개수
    analyzer_use_strict_filter = False
    analyzer_bollinger_band_mode ='normal' # 'relaxed' #'strict'
    analyzer_bollinger_band_relaxed_pct = 5.0
    analyzer_use_volume_filter = False

    # --- 1. 오래된 캐시 정리 및 캐시 파일명 정의 (뉴욕 시간대 기준) ---
    ny_timezone = pytz.timezone("America/New_York")
    today = datetime.now(ny_timezone).date()
    
    peg_status_str = "pegON" if screener_use_peg_filter else "pegOFF"
    # 캐시 파일명에 지수 이름 추가 (공백, & 제거 후 대문자)
    cleaned_index_name = screener_index_name.replace(' ', '').replace('&', '').upper()
    cache_filename = f"watchlist_{cleaned_index_name}_{today.strftime('%Y-%m-%d')}_rsi{screener_rsi_threshold}_{peg_status_str}.csv"

    print(f"--- 0단계: 오래된 캐시 파일 정리 (기준일: {today.strftime('%Y-%m-%d')} 뉴욕) ---")
    for f in os.listdir('.'):
        # 변경된 파일명 형식에 맞게 시작 부분 확인
        if f.startswith(f'watchlist_{cleaned_index_name}_') and f.endswith('.csv'):
            try:
                # 파일명에서 날짜 부분 추출 (예: watchlist_SP500_2023-10-27_...)
                file_date_str = f.split('_')[2] # 인덱스 이름이 간결해져 날짜 인덱스 변경
                file_date = datetime.strptime(file_date_str, '%Y-%m-%d').date()
                if file_date < today:
                    os.remove(f)
                    print(f"- 오래된 캐시 파일 삭제: {f}")
            except (IndexError, ValueError):
                continue

    # --- 2. 저평가 후보 종목 발굴 (Screener) ---
    watchlist_df = pd.DataFrame() # 초기화
    if use_cache and os.path.exists(cache_filename):
        print(f"\n--- 1단계: 캐시된 관심 종목 리스트 사용 ({screener_index_name}) ---")
        print(f"- 파일: {cache_filename}")
        watchlist_df = pd.read_csv(cache_filename)
    
    if watchlist_df.empty:
        print(f"\n--- 1단계: 저평가 후보 종목 신규 발굴 시작 ({screener_index_name}) ---")
        print(f"[RSI 조건] Period: {screener_rsi_period}, Threshold: < {screener_rsi_threshold}")
        if screener_use_peg_filter:
            print(f"[PEG 조건] 0 < PEG < {screener_peg_threshold}")
        else:
            print("[PEG 조건] 비활성화")
        
        undervalued_candidates = find_undervalued_stocks(
            rsi_period=screener_rsi_period,
            rsi_threshold=screener_rsi_threshold, 
            peg_threshold=screener_peg_threshold,
            use_peg_filter=screener_use_peg_filter,
            index_name=screener_index_name # 지수 이름 전달
        )
        if undervalued_candidates:
            watchlist_df = pd.DataFrame(undervalued_candidates)
            if use_cache:
                print(f"\n- 결과를 캐시 파일에 저장: {cache_filename}")
                watchlist_df.to_csv(cache_filename, index=False)

    if watchlist_df.empty:
        print("\n1단계: 저평가 후보 종목을 찾지 못했습니다. 워크플로우를 종료합니다.")
        return
    
    print("\n--- 1단계 결과: 최종 관심 종목 리스트 ---")
    print(watchlist_df.to_string(index=False))

    # --- 3. 매수 타이밍 포착 (최적화 및 반복 재시도) ---
    print("\n\n--- 2단계: 매수 타이밍 포착 시작 ---")
    print(f"[추세 조건] {"엄격 모드" if analyzer_use_strict_filter else "완화 모드"}")
    print(f"[볼린저밴드 조건] {analyzer_bollinger_band_mode} 모드 (근접률: {analyzer_bollinger_band_relaxed_pct}%) ")
    print(f"[거래량 조건] {"활성화" if analyzer_use_volume_filter else "비활성화"}")

    analyzer_rsi_threshold = analyzer_initial_rsi_threshold
    previous_rsi_threshold = 0
    final_buy_signals = []
    # 최소 신호 개수를 찾거나 최대 RSI 기준에 도달할 때까지 반복
    while analyzer_rsi_threshold <= analyzer_max_rsi_threshold and len(final_buy_signals) < analyzer_min_signals_to_find:
        print(f"\n- RSI {analyzer_rsi_threshold} 기준으로 매수 신호 분석 시도 (Period: {analyzer_rsi_period})...")
        
        eligible_df = watchlist_df[
            (watchlist_df['rsi'] < analyzer_rsi_threshold) & 
            (watchlist_df['rsi'] >= previous_rsi_threshold)
        ]
        if eligible_df.empty:
            print("  -> 이 기준 범위에 해당하는 분석 대상 종목이 없습니다. 다음 기준으로 넘어갑니다.")
            previous_rsi_threshold = analyzer_rsi_threshold
            analyzer_rsi_threshold += 5
            continue

        eligible_tickers = eligible_df['ticker'].tolist()
        print(f"  -> 분석 대상: {len(eligible_tickers)}개 종목")

        current_signals = find_buy_signals(
            eligible_tickers, 
            rsi_period=analyzer_rsi_period,
            rsi_threshold=analyzer_rsi_threshold,
            use_strict_filter=analyzer_use_strict_filter,
            bollinger_band_mode=analyzer_bollinger_band_mode,
            bollinger_band_relaxed_pct=analyzer_bollinger_band_relaxed_pct,
            use_volume_filter=analyzer_use_volume_filter
        )
        
        if current_signals:
            print(f"  -> 신호 발견! (RSI: {analyzer_rsi_threshold}, {len(current_signals)}개) ")
            final_buy_signals.extend(current_signals) # 현재 찾은 신호들을 최종 리스트에 추가
        else:
            print("  -> 신호 없음.")
        
        # 다음 반복을 위해 RSI 기준 업데이트
        previous_rsi_threshold = analyzer_rsi_threshold
        analyzer_rsi_threshold += 5

    # --- 최종 결과 출력 ---
    if not final_buy_signals:
        print(f"\n\n--- 최종 결과: 모든 RSI 기준({analyzer_initial_rsi_threshold}~{analyzer_max_rsi_threshold})에서 매수 신호를 찾지 못했습니다. ---")
        return

    print(f"\n\n--- 최종 결과: 지금 매수 신호가 포착된 종목 ({len(final_buy_signals)}개) ---")
    for ticker in final_buy_signals:
        print(f"  -> {ticker}")

if __name__ == '__main__':
    run_investment_workflow(use_cache=True)
