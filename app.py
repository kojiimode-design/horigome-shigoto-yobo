import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import requests

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

# 1. 天気予報と気温を「超強引に」取得
@st.cache_data(ttl=3600)
def get_weather_data():
    try:
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
        res = requests.get(url).json()
        
        # 3日目以降の週間データ（ここが一番安定してるぉ）
        weekly = res[1]["timeSeries"]
        w_list = weekly[0]["areas"][0]["weathers"] # 天気
        t_max = weekly[1]["areas"][0]["tempsMax"] # 最高
        t_min = weekly[1]["areas"][0]["tempsMin"] # 最低
        
        # 今日・明日のデータも補完
        w_today = res[0]["timeSeries"][0]["areas"][0]["weathers"]
        all_w = w_today + w_list[1:]
        
        return all_w, t_max, t_min
    except:
        return ["不明"]*10, ["-"]*10, ["-"]*10

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
        
        # 予報配列から取得（iがズレるのを防ぐ）
        w_text = weathers[i] if i < len(weathers) else " "
        
        # 気温（週間予報は「明日」から始まることが多いので調整）
        t_idx = i - 1 if i > 0 else 0
        ma = t_max[t_idx] if t_idx < len(t_max) and t_max[t_idx] != "" else "--"
        mi = t_min[t_idx] if t_idx < len(t_min) and t_min[t_idx] != "" else "--"
        
        # アイコン判定
        icon = "☀️" if "晴" in w_text else "☔" if "雨" in w_text else "❄️" if "雪" in w_text else "☁️"

        st.markdown(f"""
            <div class="weather-card">
                <div class="date-text">{display_date}</div>
                <div class="weather-content">
                    <div class="weather-main"><span>{icon}</span>&nbsp;{w_text[:12]}</div>
                    <div class="temp-text"><span style='color:#ff6b6b'>{ma}</span> / <span style='color:#4a90e2'>{mi}</span> ℃</div>
                </div>
                <div class="job-capsule">{job_val}</div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"読み込みエラー：{e}")
