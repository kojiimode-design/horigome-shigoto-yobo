import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import requests

# ページ設定
st.set_page_config(page_title="堀籠天気仕事予報", layout="centered")

# デザイン設定（1枚目を完全再現）
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
    .weather-main { display: flex; align-items: center; font-size: 0.8rem; color: #444; text-align: center; }
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

# 1. 天気予報と気温を「絶対に取りこぼさない」関数
@st.cache_data(ttl=600)
def get_weather_data():
    try:
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
        res = requests.get(url).json()
        
        # --- 天気を1週間分つなげる ---
        # 今日・明日
        w_short = res[0]["timeSeries"][0]["areas"][0]["weathers"]
        # 明後日以降
        w_long = res[1]["timeSeries"][0]["areas"][0]["weathers"]
        all_weathers = w_short + w_long

        # --- 気温を1週間分つなげる ---
        # 週間予報のエリア（ここから最高・最低を拾う）
        temp_area = res[1]["timeSeries"][1]["areas"][0]
        max_ts = temp_area["tempsMax"]
        min_ts = temp_area["tempsMin"]
        
        all_temps = []
        for i in range(len(all_weathers)):
            # 週間予報の気温は「明日」から始まることが多いので調整
            idx = i - 1 if i > 0 else 0
            # 安全にデータを取得
            mx = max_ts[idx] if idx < len(max_ts) and max_ts[idx] != "" else "--"
            mi = min_ts[idx] if idx < len(min_ts) and min_ts[idx] != "" else "--"
            all_temps.append(f"<span style='color:#ff6b6b'>{mx}</span> / <span style='color:#4a90e2'>{mi}</span> ℃")
            
        return all_weathers, all_temps
    except:
        return ["☁️ 取得エラー"] * 10, ["-- / -- ℃"] * 10

weathers, temps = get_weather_data()

# 2. スプレッドシート取得
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_info = st.secrets["gspread_credentials"]
    credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(st.secrets["spreadsheet_id"])
    worksheet = sh.get_worksheet(0)
    all_rows = worksheet.get_all_records()
    
    # 3. 表示
    for i, row in enumerate(all_rows):
        date_val = str(row.get('日付', ''))
        display_date = date_val.replace("2026-", "").replace("-", "/")
        job_val = str(row.get('行程', ' '))
        
        # 予報データを順番に割り当てる
        w_text = weathers[i] if i < len(weathers) else " "
        t_text = temps[i] if i < len(temps) else "-- / -- ℃"
        
        # アイコン判定
        icon = "☀️" if "晴" in w_text else "☔" if "雨" in w_text else "❄️" if "雪" in w_text else "☁️"

        st.markdown(f"""
            <div class="weather-card">
                <div class="date-text">{display_date}</div>
                <div class="weather-content">
                    <div class="weather-main"><span>{icon}</span>&nbsp;{w_text[:12]}</div>
                    <div class="temp-text">{t_text}</div>
                </div>
                <div class="job-capsule">{job_val}</div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"読み込みエラー：{e}")
