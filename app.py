import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import requests

# ページ設定（幅を狭くして中央に寄せる）
st.set_page_config(page_title="堀籠天気仕事予報", layout="centered")

# デザインをColab（1枚目）に極限まで寄せるCSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    
    .main { background-color: #f0f2f6; }
    
    /* カード全体のデザイン */
    .weather-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border-radius: 25px;
        padding: 12px 20px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        font-family: 'Noto Sans JP', sans-serif;
        border: 1px solid rgba(255,255,255,0.3);
        width: 100%;
        max-width: 500px; /* 横幅を制限 */
        margin-left: auto;
        margin-right: auto;
    }
    
    /* 日付部分 */
    .date-text {
        font-weight: bold;
        color: #4a90e2;
        width: 70px;
        font-size: 0.95rem;
    }
    
    /* 天気とアイコン */
    .weather-info {
        display: flex;
        align-items: center;
        flex-grow: 1;
        justify-content: center;
        color: #555;
        font-size: 0.85rem;
    }
    .weather-icon { font-size: 1.2rem; margin-right: 5px; }
    
    /* 行程（白いカプセル） */
    .job-capsule {
        background-color: rgba(255, 255, 255, 0.8);
        padding: 6px 15px;
        border-radius: 20px;
        font-weight: bold;
        color: #333;
        min-width: 130px;
        text-align: center;
        font-size: 0.85rem;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
    }
    
    h2 { font-family: 'Noto Sans JP', sans-serif; color: #555; margin-bottom: 30px !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center;'>📋 堀籠天気仕事予報</h2>", unsafe_allow_html=True)

# 1. 天気予報を取得（岩見沢）
@st.cache_data(ttl=3600)
def get_weather():
    try:
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
        data = requests.get(url).json()
        return data[0]["timeSeries"][0]["areas"][0]["weathers"]
    except:
        return ["不明"] * 10

weathers = get_weather()

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
        # 日付を「2/2(月)」みたいな短い形式に整形（できれば）
        # 今回はそのまま表示
        
        job_val = str(row.get('行程', ''))
        w_text = weathers[i] if i < len(weathers) else "　"
        
        # アイコン判定
        icon = "☀️" if "晴" in w_text else "☔" if "雨" in w_text else "❄️" if "雪" in w_text else "☁️"

        # HTML出力
        st.markdown(f"""
            <div class="weather-card">
                <div class="date-text">{date_val}</div>
                <div class="weather-info">
                    <span class="weather-icon">{icon}</span>
                    <span>{w_text[:10]}</span>
                </div>
                <div class="job-capsule">{job_val if job_val else "　"}</div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"読み込みエラーだぉ：{e}")
