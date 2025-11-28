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
PAGES_TO_SCRAPE = 50  # Fixed depth
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
    "AMZN": ["아마존", "amzn", "베
