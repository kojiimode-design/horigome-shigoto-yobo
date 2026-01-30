import streamlit as st
import requests
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

# ページ設定
st.set_page_config(page_title="堀籠天気仕事予報", layout="centered")

# スプレッドシート接続
def get_ss_data():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    # 後で設定する「秘密の鍵」を使って接続するぉ
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    ss = client.open("堀籠天気メモ")
    sheet = ss.get_worksheet(0)
    return sheet.get_all_values()

# 表示用デザイン
st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #74ebd5 0%, #9face6 100%); }
    .stApp { background: transparent; }
    h1 { text-shadow: 2px 2px 4px rgba(0,0,0,0.2); }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: white;'>📋 堀籠天気仕事予報</h1>", unsafe_allow_html=True)

try:
    # 行程データ取得
    all_rows = get_ss_data()[1:]
    memo_dict = {row[0].replace('/', '-'): row[1] for row in all_rows if len(row) >= 2}

    # 天気データ取得
    lat, lon = 43.1908, 141.7451
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=Asia%2FTokyo"
    weather_data = requests.get(url).json()

    w_dict = {0: "☀️ 晴れ", 1: "🌤️ ほぼ晴", 2: "⛅ 時々曇", 3: "☁️ くもり", 71: "❄️ 小雪", 73: "❄️ 雪", 75: "☃️ 強い雪"}
    weeks = ['(月)', '(火)', '(水)', '(木)', '(金)', '(土)', '(日)']

    for i in range(7):
        day_raw = weather_data["daily"]["time"][i]
        dt = datetime.strptime(day_raw, "%Y-%m-%d")
        day_key_short = f"{dt.year}-{dt.month}-{dt.day}"
        memo = memo_dict.get(day_raw, memo_dict.get(day_key_short, ""))
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            st.write(f"**{dt.month}/{dt.day} {weeks[dt.weekday()]}**")
        with col2:
            code = weather_data["daily"]["weathercode"][i]
            st.write(f"{w_dict.get(code, '☁️')}")
        with col3:
            st.info(memo if memo else "予定なし")

except Exception as e:
    st.warning("スプレッドシートの接続設定（鍵）がまだだぉ！次でやるから待っててね。")
