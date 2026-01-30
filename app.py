import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import requests

# ページ設定
st.set_page_config(page_title="堀籠天気仕事予報", layout="centered")

# CSSでデザインをColab風に改造
st.markdown("""
    <style>
    .main { background-color: #2b2b2b; }
    .weather-card {
        background: linear-gradient(180deg, #a1eafb 0%, #d1d1f0 100%);
        border-radius: 20px;
        padding: 20px;
        color: #333;
        font-family: 'sans-serif';
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .date-text { font-weight: bold; width: 80px; }
    .weather-text { flex-grow: 1; text-align: center; }
    .job-text { 
        background: rgba(255,255,255,0.7);
        padding: 5px 15px;
        border-radius: 15px;
        min-width: 150px;
        text-align: center;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; color: white;'>📋 堀籠天気仕事予報</h2>", unsafe_allow_html=True)

# 天気アイコン変換
def get_icon(w_text):
    if "晴" in w_text: return "☀️"
    if "雨" in w_text: return "☔"
    if "雪" in w_text: return "❄️"
    return "☁️"

# 1. 天気予報を取得
try:
    w_url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
    w_data = requests.get(w_url).json()
    # 岩見沢エリアの予報
    area = w_data[0]["timeSeries"][0]["areas"][0]
    weathers = area["weathers"]
    dates = ["1/30(金)", "1/31(土)", "2/1(日)", "2/2(月)", "2/3(火)", "2/4(水)", "2/5(木)"]
except:
    weathers = ["不明"] * 7
    dates = ["不明"] * 7

# 2. スプレッドシート（仕事予定）を取得
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_info = st.secrets["gspread_credentials"]
    credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(st.secrets["spreadsheet_id"])
    worksheet = sh.get_worksheet(0)
    sheet_data = pd.DataFrame(worksheet.get_all_records())
    # 日付をキーにして行程を辞書化
    job_dict = dict(zip(sheet_data['日付'], sheet_data['行程']))
except:
    job_dict = {}

# 3. デザインに合わせて表示
for i in range(len(weathers)):
    d_str = dates[i]
    # スプレッドシートの日付形式（2026-2-2等）に合わせて検索
    # 簡易的にインデックスで紐付け
    display_date = d_str
    
    # 行程を取得（とりあえず日付が合うものを入れる）
    job_key = f"2026-2-{i-1}" # ここはシートの形式に合わせる必要あり
    job_text = job_dict.get(job_key, "") 
    
    # 1枚目のスクショを再現するHTML
    st.markdown(f"""
        <div class="weather-card">
            <div class="date-text">{d_str}</div>
            <div class="weather-text">{get_icon(weathers[min(i,1)])} {weathers[min(i,1)][:5]}</div>
            <div class="job-text">{job_text if job_text else "　"}</div>
        </div>
    """, unsafe_allow_html=True)
