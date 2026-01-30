import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import requests

st.set_page_config(page_title="堀籠天気仕事予報", layout="centered")

# デザイン設定（Colab風）
st.markdown("""
    <style>
    .weather-card {
        background: linear-gradient(135deg, #a1eafb 0%, #d1d1f0 100%);
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        color: #333;
    }
    .date-box { font-weight: bold; width: 100px; font-size: 1.1em; }
    .weather-box { flex-grow: 1; text-align: center; font-size: 0.9em; }
    .job-box { 
        background: white;
        padding: 8px 15px;
        border-radius: 10px;
        min-width: 160px;
        text-align: center;
        font-weight: bold;
        color: #555;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>📋 堀籠天気仕事予報</h2>", unsafe_allow_html=True)

# 1. 天気予報を取得（岩見沢周辺）
@st.cache_data(ttl=3600)
def get_weather_info():
    try:
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
        data = requests.get(url).json()
        area = data[0]["timeSeries"][0]["areas"][0]
        return area["weathers"]
    except:
        return ["不明"] * 10

weathers = get_weather_info()

# 2. スプレッドシートから全データを取得
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_info = st.secrets["gspread_credentials"]
    credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(st.secrets["spreadsheet_id"])
    worksheet = sh.get_worksheet(0)
    
    # 全データをリストで取得
    all_rows = worksheet.get_all_records()
    
    # 3. 1行ずつカードにして表示
    for i, row in enumerate(all_rows):
        date_val = str(row.get('日付', '不明'))
        job_val = str(row.get('行程', ' '))
        
        # 天気予報は最初の2日分しかないので、それ以降は「予報なし」
        w_text = weathers[i] if i < len(weathers) else "　"
        icon = "❄️" if "雪" in w_text else "☁️" if "曇" in w_text else "☀️" if "晴" in w_text else " "

        st.markdown(f"""
            <div class="weather-card">
                <div class="date-box">{date_val}</div>
                <div class="weather-box">{icon} {w_text[:8]}</div>
                <div class="job-box">{job_val}</div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"エラーだぉ：{e}")
