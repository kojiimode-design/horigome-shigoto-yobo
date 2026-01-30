import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import requests

st.set_page_config(page_title="堀籠天気仕事予報", layout="centered")

# デザイン設定（Colab再現版）
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
    .weather-main { display: flex; align-items: center; font-size: 0.75rem; color: #555; text-align: center; }
    .temp-text { font-size: 0.8rem; color: #ff6b6b; font-weight: bold; margin-top: 2px; }
    .job-capsule {
        background-color: rgba(255, 255, 255, 0.85);
        padding: 6px 12px;
        border-radius: 15px;
        font-weight: bold;
        color: #333;
        min-width: 120px;
        text-align: center;
        font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>📋 堀籠天気仕事予報</h2>", unsafe_allow_html=True)

# 1. 天気と気温をガチで取得する関数
@st.cache_data(ttl=3600)
def get_weather_forecast():
    try:
        # 岩見沢がある空知地方の予報データ
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
        data = requests.get(url).json()
        
        # 天気（今日〜1週間分）
        w1 = data[0]["timeSeries"][0]["areas"][0]["weathers"] # 今日明日
        w2 = data[1]["timeSeries"][0]["areas"][0]["weathers"] # 3日目以降
        all_w = w1 + w2
        
        # 気温（週間予報から抽出）
        # data[1]のtimeSeries[1]に最高・最低気温のセットが入ってるぉ
        t_max = data[1]["timeSeries"][1]["areas"][0]["tempsMax"]
        t_min = data[1]["timeSeries"][1]["areas"][0]["tempsMin"]
        
        all_t = []
        for i in range(len(all_w)):
            # 週間予報の気温データは今日・明日分が空の場合があるので調整
            idx = i - 1 if i > 0 else 0 
            mx = t_max[idx] if idx < len(t_max) and t_max[idx] != "" else "--"
            mn = t_min[idx] if idx < len(t_min) and t_min[idx] != "" else "--"
            all_t.append(f"{mx} / {mn} ℃")
            
        return all_w, all_t
    except:
        return ["不明"] * 10, ["-- / -- ℃"] * 10

weathers, temps = get_weather_forecast()

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
        
        # 取得したデータを割り当て（足りない分は空白）
        w_text = weathers[i] if i < len(weathers) else " "
        t_text = temps[i] if i < len(temps) else "-- / -- ℃"
        
        # アイコン判定
        icon = "☀️" if "晴" in w_text else "☔" if "雨" in w_text else "❄️" if "雪" in w_text else "☁️" if "曇" in w_text else " "

        st.markdown(f"""
            <div class="weather-card">
                <div class="date-text">{date_val[5:] if len(date_val)>5 else date_val}</div>
                <div class="weather-content">
                    <div class="weather-main"><span>{icon}</span> {w_text[:12]}</div>
                    <div class="temp-text">{t_text}</div>
                </div>
                <div class="job-capsule">{job_val if job_val else "　"}</div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"エラーだぉ：{e}")
