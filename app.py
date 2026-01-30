import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="堀籠天気仕事予報", layout="centered")

# --- デザイン設定（こーじのこだわりを継承だぉ！） ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    .weather-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border-radius: 20px;
        padding: 10px 18px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        font-family: 'Noto Sans JP', sans-serif;
        max-width: 480px;
        margin-left: auto;
        margin-right: auto;
    }
    .date-text { font-weight: bold; width: 65px; font-size: 0.9rem; color: #555; }
    .weather-content { flex-grow: 1; display: flex; flex-direction: column; align-items: center; padding: 0 10px; }
    .weather-main { display: flex; align-items: center; font-size: 0.8rem; color: #444; }
    .temp-text { font-size: 0.85rem; font-weight: bold; margin-top: 2px; }
    .job-capsule {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 7px 15px;
        border-radius: 15px;
        font-weight: bold;
        color: #333;
        min-width: 140px;
        text-align: center;
        font-size: 0.85rem;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; color: #444;'>📋 堀籠天気仕事予報</h2>", unsafe_allow_html=True)

# --- 1. 天気データを「日付キー」で取得するロジック ---
@st.cache_data(ttl=3600)
def get_weather_dict():
    weather_map = {}
    try:
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
        res = requests.get(url).json()
        
        # 週間予報のデータを解析
        ts_week = res[1]["timeSeries"]
        times = ts_week[0]["timeDefines"]
        weathers = ts_week[0]["areas"][0]["weathers"]
        max_temps = ts_week[1]["areas"][0]["tempsMax"]
        min_temps = ts_week[1]["areas"][0]["tempsMin"]
        
        for i in range(len(times)):
            dt = datetime.fromisoformat(times[i])
            # スプレッドシートの形式「2026-2-2」に合わせるキーを作成
            date_key = f"{dt.year}-{dt.month}-{dt.day}"
            weather_map[date_key] = {
                "weather": weathers[i],
                "max": max_temps[i] if max_temps[i] != "" else "--",
                "min": min_temps[i] if min_temps[i] != "" else "--"
            }
    except:
        pass
    return weather_map

weather_dict = get_weather_dict()

# --- 2. スプレッドシート取得と表示 ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_info = st.secrets["gspread_credentials"]
    credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(st.secrets["spreadsheet_id"])
    worksheet = sh.get_worksheet(0)
    # 最初の7日間だけ表示するぉ！
    all_rows = worksheet.get_all_records()[:7] 
    
    for row in all_rows:
        date_val = str(row.get('日付', '')).strip()
        # 表示用のフォーマット (2026-2-2 -> 2/2)
        display_date = date_val.replace("2026-", "").replace("-", "/")
        job_val = str(row.get('行程', row.get('仕事内容', ' '))) # 「行程」か「仕事内容」どちらでもOK
        
        # 日付キーで天気を検索（1ミリの狂いもなく紐付け！）
        w_info = weather_dict.get(date_val, {"weather": "予報なし", "max": "--", "min": "--"})
        w_text = w_info["weather"]
        
        # アイコン判定
        icon = "☀️" if "晴" in w_text else "☔" if "雨" in w_text else "❄️" if "雪" in w_text else "☁️"

        st.markdown(f"""
            <div class="weather-card">
                <div class="date-text">{display_date}</div>
                <div class="weather-content">
                    <div class="weather-main"><span>{icon}</span>&nbsp;{w_text[:10]}</div>
                    <div class="temp-text"><span style='color:#ff6b6b'>{w_info['max']}</span> / <span style='color:#4a90e2'>{w_info['min']}</span> ℃</div>
                </div>
                <div class="job-capsule">{job_val}</div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"読み込みエラーだぉ、こーじ！：{e}")
