import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import requests

st.set_page_config(page_title="堀籠天気仕事予報", layout="centered")

# デザイン設定（1枚目の再現）
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

# 1. 天気予報と気温を「安全に」取得
@st.cache_data(ttl=3600)
def get_weather_data():
    try:
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
        res = requests.get(url).json()
        
        # 週間予報の「天気」と「気温」の箱を特定
        weekly_weathers = res[1]["timeSeries"][0]["areas"][0]["weathers"]
        max_temps = res[1]["timeSeries"][1]["areas"][0]["tempsMax"]
        min_temps = res[1]["timeSeries"][1]["areas"][0]["tempsMin"]
        
        return weekly_weathers, max_temps, min_temps
    except:
        # 万が一失敗しても止まらないようにダミーを返す
        return ["☁️ 曇り"]*10, ["-"]*10, ["-"]*10

weathers, t_max, t_min = get_weather_data()

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
        
        # 週間予報からデータを抽出
        w_text = weathers[i] if i < len(weathers) else " "
        ma = t_max[i] if i < len(t_max) and t_max[i] != "" else "--"
        mi = t_min[i] if i < len(t_min) and t_min[i] != "" else "--"
        
        # アイコン判定
        icon = "☀️" if "晴" in w_text else "☔" if "雨" in w_text else "❄️" if "雪" in w_text else "☁️"

        st.markdown(f"""
            <div class="weather-card">
                <div class="date-text">{display_date}</div>
                <div class="weather-content">
                    <div class="weather-main"><span>{icon}</span>&nbsp;{w_text[:10]}</div>
                    <div class="temp-text"><span style='color:#ff6b6b'>{ma}</span> / <span style='color:#4a90e2'>{mi}</span> ℃</div>
                </div>
                <div class="job-capsule">{job_val}</div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"読み込みエラー：{e}")
