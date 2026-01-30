import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import requests

# ページ設定
st.set_page_config(page_title="堀籠天気仕事予報", layout="centered")

# デザイン設定（Colabデザインを完全再現）
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
    .date-text { font-weight: bold; width: 65px; font-size: 0.9rem; }
    .blue-day { color: #4a90e2; } .red-day { color: #ff6b6b; } .gray-day { color: #555; }
    .weather-content { flex-grow: 1; display: flex; flex-direction: column; align-items: center; padding: 0 10px; }
    .weather-main { display: flex; align-items: center; font-size: 0.8rem; color: #555; }
    .temp-text { font-size: 0.85rem; font-weight: bold; margin-top: 2px; }
    .job-capsule {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 7px 15px;
        border-radius: 15px;
        font-weight: bold;
        color: #333;
        min-width: 135px;
        text-align: center;
        font-size: 0.85rem;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>📋 堀籠天気仕事予報</h2>", unsafe_allow_html=True)

# 1. 天気予報と気温を確実に取得
@st.cache_data(ttl=3600)
def get_weather_data():
    try:
        # 岩見沢を含む空知地方のデータ
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
        data = requests.get(url).json()
        
        # 今日・明日の予報
        w_today_tomorrow = data[0]["timeSeries"][0]["areas"][0]["weathers"]
        # 週間予報（3日目以降）
        w_weekly = data[1]["timeSeries"][0]["areas"][0]["weathers"]
        all_weathers = (w_today_tomorrow + w_weekly)[:10]

        # 気温データ（週間予報のエリアから取得）
        # data[1]のtimeSeries[1]が最高・最低気温
        temp_areas = data[1]["timeSeries"][1]["areas"][0]
        max_temps = temp_areas["tempsMax"]
        min_temps = temp_areas["tempsMin"]
        
        all_temps = []
        for i in range(len(all_weathers)):
            # 週間予報の配列は今日を含まない場合があるため調整
            t_idx = i - 1 if i > 0 else 0
            ma = max_temps[t_idx] if t_idx < len(max_temps) and max_temps[t_idx] != "" else "--"
            mi = min_temps[t_idx] if t_idx < len(min_temps) and min_temps[t_idx] != "" else "--"
            all_temps.append(f"<span style='color:#ff6b6b'>{ma}</span> / <span style='color:#4a90e2'>{mi}</span> ℃")
            
        return all_weathers, all_temps
    except:
        return ["不明"] * 10, ["-- / -- ℃"] * 10

weathers, temps = get_weather_data()

# 2. スプレッドシート取得
try:
    creds_info = st.secrets["gspread_credentials"]
    credentials = Credentials.from_service_account_info(creds_info, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(st.secrets["spreadsheet_id"])
    worksheet = sh.get_worksheet(0)
    all_rows = worksheet.get_all_records()
    
    # 3. 表示
    for i, row in enumerate(all_rows):
        date_val = str(row.get('日付', ''))
        job_val = str(row.get('行程', ''))
        
        # 日付の見た目調整（2026-2-2 -> 2/2）
        display_date = date_val.replace("2026-", "").replace("-", "/")
        
        w_text = weathers[i] if i < len(weathers) else " "
        t_text = temps[i] if i < len(temps) else "-- / -- ℃"
        
        # アイコン判定
        icon = "☀️" if "晴" in w_text else "☔" if "雨" in w_text else "❄️" if "雪" in w_text else "☁️" if "曇" in w_text else " "

        st.markdown(f"""
            <div class="weather-card">
                <div class="date-text gray-day">{display_date}</div>
                <div class="weather-content">
                    <div class="weather-main"><span>{icon}</span>&nbsp;{w_text[:10]}</div>
                    <div class="temp-text">{t_text}</div>
                </div>
                <div class="job-capsule">{job_val if job_val else "　"}</div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"読み込みエラーだぉ：{e}")
