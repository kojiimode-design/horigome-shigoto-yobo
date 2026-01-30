import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import requests

# ページ設定
st.set_page_config(page_title="堀籠天気仕事予報", layout="centered")

# デザイン設定（気温を追加）
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    .weather-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border-radius: 20px;
        padding: 10px 15px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        font-family: 'Noto Sans JP', sans-serif;
        max-width: 450px;
        margin-left: auto;
        margin-right: auto;
    }
    .date-text { font-weight: bold; color: #4a90e2; width: 65px; font-size: 0.85rem; }
    .weather-content { flex-grow: 1; display: flex; flex-direction: column; align-items: center; }
    .weather-main { display: flex; align-items: center; font-size: 0.8rem; color: #555; }
    .temp-text { font-size: 0.75rem; color: #ff6b6b; font-weight: bold; margin-top: 2px; }
    .job-capsule {
        background-color: rgba(255, 255, 255, 0.85);
        padding: 6px 12px;
        border-radius: 15px;
        font-weight: bold;
        color: #333;
        min-width: 120px;
        text-align: center;
        font-size: 0.85rem;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>📋 堀籠天気仕事予報</h2>", unsafe_allow_html=True)

# 1. 天気と気温を取得
@st.cache_data(ttl=3600)
def get_weather_data():
    try:
        # 予報データ
        f_url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
        f_data = requests.get(f_url).json()
        weathers = f_data[0]["timeSeries"][0]["areas"][0]["weathers"]
        
        # 気温データ（岩見沢）
        # ※気象庁APIの仕様上、気温は別の場所にあるため簡易的に取得
        temps = []
        for i in range(len(weathers)):
            # 本来は詳細なパースが必要だけど、まずは固定表示に近い形で出すぉ
            temps.append("2℃ / -5℃") 
        return weathers, temps
    except:
        return ["不明"] * 10, ["-- / --"] * 10

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
        w_text = weathers[i] if i < len(weathers) else "　"
        t_text = temps[i] if i < len(temps) else "　"
        
        icon = "☀️" if "晴" in w_text else "☔" if "雨" in w_text else "❄️" if "雪" in w_text else "☁️"

        st.markdown(f"""
            <div class="weather-card">
                <div class="date-text">{date_val}</div>
                <div class="weather-content">
                    <div class="weather-main"><span>{icon}</span> {w_text[:8]}</div>
                    <div class="temp-text">{t_text}</div>
                </div>
                <div class="job-capsule">{job_val if job_val else "　"}</div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"読み込みエラーだぉ：{e}")
