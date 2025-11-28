Here is the code as plain text that you can copy:

Python

import streamlit as st
import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
import pandas as pd
import time
import yfinance as yf
from datetime import datetime
import pytz
import concurrent.futures

# --- CONFIGURATION ---

# 1. CONSTANTS
PAGES_TO_SCRAPE = 50  # Fixed depth (approx 2,500 posts)
REFRESH_SECONDS = 300 # 5 Minutes
MAX_WORKERS = 10      # Speed boost: Scrapes 10 pages at once

# 2. MANUAL KOREAN MAP (Priority List)
MANUAL_MAP = {
    "BMNR": ["bmnr", "비트마인", "비엠엔알", "이더리움"],
    "RGTI": ["rgti", "리게티", "양자", "퀀텀"],
    "NBIS": ["nbis", "네비우스", "얀덱스", "yandex"],
    "CRWV": ["crwv", "코어위브"],
    "OKLO": ["oklo", "오클로", "알트만", "원전"],
    "IREN": ["iren", "아이리스", "이렌", "채굴"],
    "SBET": ["sbet", "샤프링크", "에스벳"],
    "SOXL": ["속슬", "soxl", "필반도체", "3배", "반도체3배"],
    "SOXS": ["속스", "soxs", "숏슬", "반도체숏"],
    "TQQQ": ["티큐", "tqqq", "나스닥3배"],
    "SQQQ": ["스큐", "sqqq", "숏큐", "나스닥숏"],
    "SCHD": ["슈드", "schd", "배당", "성장주"],
    "JEPI": ["제피", "jepi", "월배당"],
    "TMF":  ["티엠에프", "tmf", "채권3배"],
    "TMV":  ["티엠브이", "tmv"],
    "BOIL": ["보일", "boil", "가스"],
    "KOLD": ["콜드", "kold", "가스숏"],
    "YINN": ["인", "yinn", "중국3배"],
    "YANG": ["양", "yang", "중국숏"],
    "TSLA": ["테슬라", "테슬형", "tsla", "머스크", "일론", "전기차", "천슬라"],
    "NVDA": ["엔비디아", "엔비", "nvda", "황회장", "젠슨황", "가죽자켓"],
    "AAPL": ["애플", "aapl", "사과", "팀쿡"],
    "MSFT": ["마소", "msft", "마이크로소프트"],
    "GOOGL": ["구글", "googl", "알파벳", "갓글"],
    "AMZN": ["아마존", "amzn", "베조스"],
    "META": ["메타", "meta", "페이스북", "주커버그"],
    "NFLX": ["넷플", "nflx", "넷플릭스"],
    "AMD":  ["암드", "amd", "리사수"],
    "INTC": ["인텔", "intc"],
    "AVGO": ["브로드컴", "avgo"],
    "TSM":  ["티에스엠", "tsm", "대만"],
    "PLTR": ["팔란티어", "pltr", "팔란"],
    "SMCI": ["슈마컴", "smci", "슈퍼마이크로"],
    "MU":   ["마이크론", "mu"],
    "IONQ": ["아이온큐", "아큐", "ionq", "김정상"],
    "COIN": ["코인베이스", "coin", "코베"],
    "MSTR": ["마이크로스트래티지", "마스", "mstr", "세일러"],
    "GME":  ["게임스탑", "gme", "겜스"],
    "AMC":  ["에이엠씨", "amc"],
    "RKLB": ["로켓랩", "rklb", "로켓"],
    "ASTS": ["에스티", "asts", "스페이스모바일"],
    "JOBY": ["조비", "joby"],
    "LCID": ["루시드", "lcid"],
    "RIVN": ["리비안", "rivn"],
    "MULN": ["뮬런", "muln"],
    "NKLA": ["니콜라", "nkla"],
    "BYND": ["bynd", "비욘드미트", "비욘드", "콩고기"],
    "CPNG": ["쿠팡", "cpng"],
    "O":    ["리얼티인컴", "리얼티", "월배당", "o"],
}

# 3. English words to ignore
IGNORE_WORDS = {
    'ETF', 'QQQ', 'AI', 'CEO', 'FOMC', 'CPI', 'PPI', 'GDP', 'VS', 'US', 'FED', 
    'SEC', 'IPO', 'PER', 'EPS', 'YOLO', 'LONG', 'SHORT', 'HOLD', 'BUY', 'SELL',
    'POV', 'USA', 'KRW', 'USD', 'NEWS', 'DCA', 'IMF', 'IRP', 'ISA', 'OTM', 'ITM',
    'GOD', 'RIP', 'WTF', 'OMG', 'BIG', 'PUT', 'CALL', 'MAX', 'MIN', 'ONE', 'TWO',
    'WOW', 'LOL', 'NEW', 'NOW', 'HOT', 'TOP', 'BEST', 'END', 'RUN', 'FLY', 'SEE',
    'WAY', 'YES', 'NO', 'AGAIN', 'TODAY', 'WEEK', 'MONTH', 'YEAR', 'TIME', 'LOVE',
    'ARE', 'CAN', 'CAT', 'EAT', 'BEAT', 'FUN', 'HAS', 'ALL', 'AGO', 'AWAY',
    'BET', 'BOX', 'CAR', 'CASH', 'DAY', 'DIG', 'DOG', 'DOOR', 'DRY', 'EYE',
    'FAT', 'FIT', 'FLY', 'FOX', 'GAS', 'GET', 'GO', 'GOLD', 'GOOD', 'GUY',
    'HE', 'HER', 'HEY', 'HIM', 'HIS', 'HOP', 'HOT', 'ICE', 'INK', 'JOB',
    'KEY', 'KIDS', 'LAW', 'LET', 'LOW', 'MAN', 'MAP', 'MET', 'MOM', 'NET',
    'OIL', 'OLD', 'OUT', 'OWN', 'PAY', 'PET', 'PLAY', 'RAW', 'RED', 'RUN',
    'SAD', 'SAFE', 'SAW', 'SAY', 'SEA', 'SEE', 'SET', 'SKY', 'SON', 'SUN',
    'TAX', 'TEA', 'TEN', 'THE', 'TIE', 'TOO', 'TOP', 'TRY', 'TWO', 'USE',
    'VAN', 'WAR', 'WAY', 'WE', 'WET', 'WIN', 'WOW', 'YES', 'YET', 'YOU', 'ZOO',
    'ART', 'ANT', 'BUG', 'BUS', 'CAP', 'CUT', 'DID', 'EGO', 'ERA', 'FAR',
    'FEW', 'FIX', 'FLU', 'FOG', 'GAP', 'GYM', 'HAT', 'HIT', 'HUG', 'HUT',
    'ILL', 'JAR', 'JET', 'JOY', 'KIT', 'LID', 'LIP', 'LOG', 'LOT', 'MAD',
    'MIX', 'MUD', 'MUG', 'NAP', 'NOD', 'NUT', 'OAK', 'ODD', 'OFF', 'PAN',
    'PEN', 'PIE', 'PIG', 'PIN', 'PIT', 'POD', 'POP', 'POT', 'PRO', 'RAG',
    'RAT', 'RIB', 'RID', 'RIG', 'RIM', 'RIP', 'ROD', 'ROT', 'RUB', 'RUG',
    'RUM', 'RUT', 'SAP', 'SIP', 'SIT', 'SIX', 'SKI', 'SOB', 'SOD', 'SOW',
    'SOY', 'SPA', 'SPY', 'SUB', 'SUM', 'TAB', 'TAG', 'TAN', 'TAP', 'TAR',
    'TIP', 'TOE', 'TON', 'TOW', 'TOY', 'TUB', 'TUG', 'URN', 'VET', 'VOW',
    'WAX', 'WEB', 'WED', 'WIG', 'WIT', 'WOE', 'WOK', 'WON', 'YAM', 'YAP',
    'YEA', 'YEN', 'YIP', 'ZIP', 'MEME', 'LIFE', 'LIVE', 'LOVE', 'HOPE', 'NEXT',
    'FAST', 'SAFE', 'BEST', 'REAL', 'TRUE', 'MAIN', 'POST', 'READ', 'LOOK',
    'HEAR', 'TELL', 'TALK', 'WALK', 'OPEN', 'SHUT', 'STOP', 'WAIT', 'STAY',
    'GROW', 'HELP', 'SEND', 'PICK', 'KEEP', 'HOLD', 'FIND', 'FALL', 'TURN',
    'MOVE', 'MEET', 'LEAD', 'LATE', 'HARD', 'EASY', 'COOL', 'COLD', 'WARM',
    'HIGH', 'DEEP', 'WIDE', 'LONG', 'FULL', 'FREE', 'RICH', 'POOR', 'NICE',
    'KIND', 'FAIR', 'FINE', 'BLUE', 'CME', 'CS', 'GS', 'MS', 'C', 'A', 'F', 'ONE'
}

# --- PAGE CONFIG ---
st.set_page_config(page_title="Korean Ant Sentiment Tracker", page_icon="🐜", layout="wide")

# --- DATA LOADING ---
@st.cache_data(ttl=3600)
def load_sec_tickers():
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {"User-Agent": "StreamlitDashboard contact@example.com"}
    sec_map = {} 
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            suffixes = [" Inc.", " Corp.", " Corporation", " Ltd", " Co.", " PLC", " Group", " Holdings"]
            for entry in data.values():
                ticker = entry['ticker'].upper()
                raw_title = entry['title']
                clean = raw_title
                for s in suffixes:
                    clean = clean.replace(s, "").replace(s.lower(), "")
                clean = clean.strip().lower()
                sec_map[ticker] = [ticker.lower()]
                if len(clean) > 3:
                    sec_map[ticker].append(clean)
            return sec_map
        return {}
    except:
        return {}

@st.cache_data(ttl=300)
def get_price_changes(ticker_list):
    if not ticker_list: return {}
    tickers_str = " ".join(ticker_list)
    changes = {}
    try:
        data = yf.download(tickers_str, period="5d", progress=False)
        if 'Close' in data:
            closes = data['Close']
            def calc_change(series):
                if len(series) >= 2:
                    return ((series.iloc[-1] - series.iloc[-2]) / series.iloc[-2]) * 100
                return None
            if isinstance(closes, pd.DataFrame):
                for ticker in ticker_list:
                    try:
                        changes[ticker] = calc_change(closes[ticker].dropna())
                    except: changes[ticker] = None
            elif isinstance(closes, pd.Series):
                changes[ticker_list[0]] = calc_change(closes.dropna())
    except: pass
    return changes

# --- HELPER TO SCRAPE ONE PAGE ---
def scrape_single_page(gallery_id, page, headers):
    url = "https://gall.dcinside.com/mgallery/board/lists"
    params = {'id': gallery_id, 'page': page}
    titles = []
    try:
        r = requests.get(url, headers=headers, params=params, timeout=5)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            for row in soup.select('.gall_list .ub-content'):
                t = row.select_one('.gall_tit a')
                if t: titles.append(re.sub(r'\[\d+\]$', '', t.text.strip()).strip())
    except: pass
    return titles

# --- SCRAPING FUNCTIONS (PARALLEL) ---
@st.cache_data(ttl=60)
def scrape_dc_gallery_parallel(gallery_id, pages=50):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
    all_titles = []
    
    # Use ThreadPoolExecutor to fetch pages in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_page = {executor.submit(scrape_single_page, gallery_id, p, headers): p for p in range(1, pages + 1)}
        for future in concurrent.futures.as_completed(future_to_page):
            try:
                data = future.result()
                all_titles.extend(data)
            except Exception as exc:
                pass
                
    return all_titles

def process_sentiment(titles, sec_map):
    ticker_counter = Counter()
    
    full_map = sec_map.copy()
    for k, v in MANUAL_MAP.items():
        if k in full_map: full_map[k] = list(set(full_map[k] + v))
        else: full_map[k] = v

    for title in titles:
        title_lower = title.lower()
        found = set()
        
        for ticker, keywords in full_map.items():
            for k in keywords:
                if len(k) > 2 and k in title_lower: 
                    found.add(ticker)
                    break
        
        for cand in re.findall(r'\b[A-Z]{2,5}\b', title):
            if cand in full_map and cand not in IGNORE_WORDS:
                found.add(cand)
        
        ticker_counter.update(found)

    return ticker_counter, titles

# --- DASHBOARD LOGIC ---
st.title("🐜 Korean Ant Sentiment Tracker")

# Get Current Time (EST)
tz = pytz.timezone('US/Eastern')
now = datetime.now(tz).strftime("%Y-%m-%d %I:%M:%S %p %Z")
st.caption(f"Last Updated: **{now}** | Updates automatically every 5 minutes.")

# --- SIDEBAR (Minimal) ---
with st.sidebar:
    st.header("Settings")
    gallery = st.selectbox("Target Gallery", ["tenbagger", "stockus", "nasdaq", "bitcoins"], index=0)
    st.info(f"Depth: Fixed at {PAGES_TO_SCRAPE} pages")
    st.info("Mode: Automatic Refresh")

# --- MAIN EXECUTION ---
# No button check, just run immediately
with st.spinner(f"Scraping {PAGES_TO_SCRAPE} pages from DC Inside..."):
    # Load Data
    sec_map = load_sec_tickers()
    titles = scrape_dc_gallery_parallel(gallery, PAGES_TO_SCRAPE)

    if titles:
        # Process
        t_counts, raw = process_sentiment(titles, sec_map)
        
        # DataFrame
        df = pd.DataFrame.from_dict(t_counts, orient='index', columns=['Mentions']).sort_values('Mentions', ascending=False).head(20)
        
        # Prices
        if not df.empty:
            top_tickers = df.index.tolist()
            price_changes = get_price_changes(top_tickers)
            df['% Change'] = df.index.map(price_changes)

        # UI
        st.success(f"Analyzed {len(titles)} posts.")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🏆 Leaderboard")
            st.bar_chart(df['Mentions'], color="#FF4B4B")
            
        with col2:
            st.subheader("📊 Detailed Counts")
            if not df.empty:
                def color_change(val):
                    if pd.isna(val): return 'color: gray'
                    color = '#4CAF50' if val > 0 else '#FF4B4B' if val < 0 else 'gray'
                    return f'color: {color}'

                styled_df = df.style.map(color_change, subset=['% Change']).format({'% Change': lambda x: f'{x:+.2f}%' if pd.notnull(x) else 'N/A'})
                st.dataframe(styled_df, use_container_width=True)
            else:
                st.info("No tickers found.")

        with st.expander("Raw Titles"):
            st.write(raw)

    # AUTO REFRESH LOOP
    time.sleep(REFRESH_SECONDS)
    st.rerun()
