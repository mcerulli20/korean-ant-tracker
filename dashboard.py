import streamlit as st
import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
import pandas as pd
import time

# --- CONFIGURATION ---
# 1. YOUR CUSTOM TICKER LIST (Embedded directly here)
# Format: "TICKER": ["korean_slang", "lowercase", "other_nickname"]
TICKER_MAP = {
    # --- YOUR REQUESTED STOCKS ---
    "BMNR": ["bmnr", "비트마인", "비엠엔알", "이더리움"],
    "RGTI": ["rgti", "리게티", "양자", "퀀텀"],
    "NBIS": ["nbis", "네비우스", "얀덱스", "yandex"],
    "CRWV": ["crwv", "코어위브"],
    "OKLO": ["oklo", "오클로", "알트만", "원전"],

    # --- LEVERAGED ETFs (The Kings of DC Inside) ---
    "SOXL": ["속슬", "soxl", "필반도체", "3배", "반도체3배"],
    "SOXS": ["속스", "soxs", "숏슬", "반도체숏"],
    "TQQQ": ["티큐", "tqqq", "나스닥3배"],
    "SQQQ": ["스큐", "sqqq", "숏큐", "나스닥숏"],
    "SCHD": ["슈드", "schd", "배당"],
    "JEPI": ["제피", "jepi"],

    # --- BIG TECH & POPULAR ---
    "TSLA": ["테슬라", "테슬형", "tsla", "머스크", "일론"],
    "NVDA": ["엔비디아", "엔비", "nvda", "황회장"],
    "AAPL": ["애플", "aapl", "사과", "팀쿡"],
    "MSFT": ["마소", "msft", "마이크로소프트"],
    "GOOGL": ["구글", "googl", "알파벳"],
    "AMZN": ["아마존", "amzn"],
    "IONQ": ["아이온큐", "아큐", "ionq"],
    "PLTR": ["팔란티어", "pltr"],
    "COIN": ["코인베이스", "coin", "코베"],
    "MSTR": ["마이크로스트래티지", "마스", "mstr"],
    "GME":  ["게임스탑", "gme", "겜스"],
}

# 2. English words to ignore in "Auto Discovery"
IGNORE_WORDS = {
    'ETF', 'QQQ', 'AI', 'CEO', 'FOMC', 'CPI', 'PPI', 'GDP', 'VS', 'US', 'FED', 
    'SEC', 'IPO', 'PER', 'EPS', 'YOLO', 'LONG', 'SHORT', 'HOLD', 'BUY', 'SELL',
    'POV', 'USA', 'KRW', 'USD', 'NEWS', 'DCA', 'IMF', 'IRP', 'ISA', 'OTM', 'ITM',
    'GOD', 'RIP', 'WTF', 'OMG', 'BIG', 'PUT', 'CALL', 'MAX', 'MIN', 'ONE', 'TWO',
    'WOW', 'LOL', 'NEW', 'NOW', 'HOT', 'TOP', 'BEST', 'END', 'RUN', 'FLY', 'SEE',
    'WAY', 'YES', 'NO', 'AGAIN', 'TODAY', 'WEEK', 'MONTH', 'YEAR', 'TIME', 'LOVE'
}

# 3. Korean words to ignore in "Mystery Trend Spotter"
KOREAN_STOPWORDS = {
    '오늘', '지금', '진짜', '이거', '근데', '하는', '내가', '존나', '시발', 'ㅋㅋ', 'ㅎㅎ',
    'ㅠㅠ', '매수', '매도', '사람', '생각', '미장', '국장', '주식', '어떻게', '왜', '좀',
    '다시', '보면', '가즈아', '오늘의', '미국', '달러', '코인', '비트', '나스닥', '있는',
    '하고', '아니', '그냥', '많이', '너무', '개미', '형들', '갈까', '말까', '언제', '역시',
    '이제', '이렇게', '지수', '하락', '상승', '본장', '프리', '거래', '수익', '손실', '제발',
    '나는', '오를', '내릴', '롱충', '숏충', '같다', '같은', '해서', '하면', '오르', '내리'
}

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Korean Ant Sentiment Tracker",
    page_icon="🐜",
    layout="wide"
)

# --- SCRAPING FUNCTIONS ---
@st.cache_data(ttl=60)
def scrape_dc_gallery(gallery_id, pages=10, mode="all"):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    base_url = "https://gall.dcinside.com/mgallery/board/lists"
    all_titles = []
    
    progress_text = st.empty()
    progress_bar = st.progress(0)
    
    for page in range(1, pages + 1):
        progress_text.text(f"🐜 Collecting Page {page}/{pages}...")
        params = {'id': gallery_id, 'page': page}
        if mode == "recommend":
            params['exception_mode'] = 'recommend'

        try:
            response = requests.get(base_url, headers=headers, params=params, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                rows = soup.select('.gall_list .ub-content')
                for row in rows:
                    title_element = row.select_one('.gall_tit a')
                    if title_element:
                        full_text = title_element.text.strip()
                        # Clean title: Remove [Reply Count] like [32]
                        clean_title = re.sub(r'\[\d+\]$', '', full_text).strip()
                        if clean_title:
                            all_titles.append(clean_title)
            time.sleep(0.15) 
        except Exception as e:
            st.error(f"Error on page {page}: {e}")
        
        progress_bar.progress(page / pages)
    
    progress_text.empty()
    progress_bar.empty()
    return all_titles

def process_sentiment(titles):
    ticker_counter = Counter()
    word_counter = Counter()
    
    # Create a set of all known keywords (tickers + slang) to exclude them from the "Unknown" list
    all_known_keywords = set()
    for keywords in TICKER_MAP.values():
        for k in keywords:
            all_known_keywords.add(k)

    for title in titles:
        title_lower = title.lower()
        found_in_title = set()
        
        # 1. Known Ticker Check (Map)
        for ticker, keywords in TICKER_MAP.items():
            for keyword in keywords:
                if keyword in title_lower:
                    found_in_title.add(ticker)
                    break 
        
        # 2. Auto Discovery (English Uppercase Words)
        # Regex finds 2-5 letter uppercase words (e.g. RGTI, TSLA)
        candidates = re.findall(r'\b[A-Z]{2,5}\b', title)
        for cand in candidates:
            if cand not in IGNORE_WORDS and cand not in found_in_title:
                # If we found it via auto-discovery, treat it as a hit
                # But check if we already mapped it to a key to avoid duplicates
                if cand in TICKER_MAP:
                    found_in_title.add(cand)
                else:
                    found_in_title.add(cand)

        ticker_counter.update(found_in_title)

        # 3. Mystery Word Spotter (Korean Only)
        # This finds high-frequency Korean words that are NOT in your ticker list yet.
        words = title_lower.split()
        for word in words:
            # Remove punctuation
            word = re.sub(r'[^\w\s]', '', word)
            
            # Logic: Must be Korean AND not a known ticker keyword AND not a stopword
            if re.search(r'[가-힣]+', word): 
                if word not in all_known_keywords and word not in KOREAN_STOPWORDS:
                    word_counter[word] += 1

    return ticker_counter, word_counter, titles

# --- DASHBOARD UI ---
st.title("🐜 Korean Ant Sentiment Tracker")
st.markdown("""
Tracking real-time mentions on **DC Inside (Mijugal)**.  
Includes **Auto-Discovery** for unknown tickers + **Mystery Word** spotting.
""")

with st.sidebar:
    st.header("⚙️ Scanner Settings")
    gallery_id = st.selectbox("Target Gallery", ["tenbagger", "stockus", "nasdaq", "bitcoins"], index=0)
    pages = st.slider("Depth (Pages)", 1, 100, 10, help="50 pages ≈ 2,500 posts.")
    mode = st.radio("Filter Mode", ["all", "recommend"], index=0, format_func=lambda x: "🔥 New Posts (High Vol)" if x == "all" else "💎 Concept (Best Of)")
    st.divider()
    if st.button("🚀 START SCAN", type="primary", use_container_width=True):
        st.session_state['run'] = True

# --- RESULTS ---
if st.session_state.get('run'):
    with st.spinner("Scraping DC Inside..."):
        titles = scrape_dc_gallery(gallery_id, pages, mode)
    
    if titles:
        ticker_counts, word_counts, raw_titles = process_sentiment(titles)
        
        # Create DataFrames
        df_tickers = pd.DataFrame.from_dict(ticker_counts, orient='index', columns=['Mentions']).sort_values(by='Mentions', ascending=False).head(20)
        df_words = pd.DataFrame.from_dict(word_counts, orient='index', columns=['Count']).sort_values(by='Count', ascending=False).head(20)
        
        # Display Results
        st.success(f"Successfully analyzed {len(titles)} posts!")
        
        col1, col2 = st.columns([1.5, 1])
        
        with col1:
            st.subheader("🏆 Top Identified Tickers")
            if not df_tickers.empty:
                st.bar_chart(df_tickers, color="#FF4B4B")
            else:
                st.info("No known tickers found. Try increasing depth.")

        with col2:
            st.subheader("❓ Mystery Trend Spotter")
            st.caption("Top Korean words NOT in your ticker map. If you see a stock name here, add it to the code!")
            st.dataframe(df_words, use_container_width=True)

        with st.expander("🔍 Inspect Raw Post Titles"):
            st.write(raw_titles)
    else:
        st.error("No data retrieved.")