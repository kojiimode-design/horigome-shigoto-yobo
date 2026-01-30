import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import requests
from datetime import datetime

# --- ページ設定 ---
st.set_page_config(page_title="堀籠天気仕事予報", layout="centered")

# --- デザイン設定（Colabのデザインをブラウザで再現だぉ！） ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    
    /* 全体背景 */
    .main-container {
        background-color: #333; /* 背景は暗めにしてカードを目立たせるぉ */
        padding: 20px;
        border-radius: 40px;
    }

    /* メインの大きなカード */
    .colab-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border-radius: 35px;
        padding: 25px 30px;
        font-family: 'Noto Sans JP', sans-serif;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        max-width: 600px;
        margin: auto;
    }
    
    /* 1日分の行 */
    .day-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.4);
    }
    .day-row:last-child { border-bottom: none; }

    /* 日付 (1/30 (金) 形式) */
    .date-text { width: 100px; font-weight: bold; font-size: 0.95rem; }
    .sat { color: #4a90e2; } 
    .sun { color: #ff6b6b; } 

    /* 天気と気温の並び */
    .weather-info { flex-grow: 1; display: flex; align-items: center; justify-content: center; gap: 5px; }
    .temp-max { color: #ff6b6b; font-weight: bold; }
    .temp-min { color: #4a90e2; font-weight: bold; }

    /* 仕事内容のカプセル */
    .job-capsule {
        background: rgba(255, 255, 255, 0.7);
        padding: 6px 15px;
        border-radius: 15px;
        min-width: 150px;
        text-align: center;
        font-weight: bold;
        font-size: 0.85rem;
        color: #333;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. 天気と気温を読み込む最強ロジックだぉ ---
@st.cache_data(ttl=3600)
def get_weather_data():
    weather_map = {}
    try:
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
        res = requests.get(url).json()
        
        # 週間予報から日付・天気・気温を取得
        ts_week = res[1]["timeSeries"]
        w_times = ts_week[0]["timeDefines"]
        w_weathers = ts_week[0]["areas"][0]["weathers"]
        w_max = ts_week[1]["areas"][0].get("tempsMax", ["--"] * len(w_times))
        w_min = ts_week[1]["areas"][0].get("tempsMin", ["--"] * len(w_times))
        
        for i in range(len(w_times)):
            dt = datetime.fromisoformat(w_times[i])
            date_key = f"{dt.year}-{dt.month}-{dt.day}"
            weather_map[date_key] = {
                "w": w_weathers[i],
                "ma": w_max[i] if w_max[i] != "" else "--",
                "mi": w_min[i] if w_min[i] != "" else "--"
            }
    except: pass
    return weather_map

weather_dict = get_weather_data()

# --- 2. スプレッドシート読み込みと表示 ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_info = st.secrets["gspread_credentials"]
    credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
    gc = gspread.authorize(credentials)
    worksheet = gc.open_by_key(st.secrets["spreadsheet_id"]).get_worksheet(0)
    
    # 週間分(7日)を取得
    all_rows = worksheet.get_all_records()[:7] 

    # Colabカード開始
    html = '<div class="colab-card">'
    html += '<h2 style="text-align: center; color: #555; margin-bottom: 20px;">📋 堀籠天気仕事予報</h2>'

    for row in all_rows:
        date_val = str(row.get('日付', '')).strip()
        try:
            dt = pd.to_datetime(date_val)
            wd = ["月", "火", "水", "木", "金", "土", "日"][dt.weekday()]
            wd_class = "sat" if dt.weekday() == 5 else "sun" if dt.weekday() == 6 else ""
            display_date = f"{dt.month}/{dt.day} ({wd})"
            match_key = f"{dt.year}-{dt.month}-{dt.day}"
        except:
            display_date, match_key, wd_class = date_val, date_val, ""

        # 天気情報を取得
        w_info = weather_dict.get(match_key, {"w": "予報なし", "ma": "--", "mi": "--"})
        w_text = w_info["w"]
        icon = "☀️" if "晴" in w_text else "☔" if "雨" in w_text else "❄️" if "雪" in w_text else "☁️"
        
        job_val = str(row.get('行程', row.get('仕事内容', ' ')))

        # 1行分のHTML
        html += f"""
            <div class="day-row">
                <div class="date-text {wd_class}">{display_date}</div>
                <div class="weather-info">
                    <span>{icon}</span>
                    <span style="font-size:0.7rem; width:50px; text-align:center;">{w_text[:5]}</span>
                    <span class="temp-max">{w_info['ma']}</span> / <span class="temp-min">{w_info['mi']}</span>
                </div>
                <div class="job-capsule">{job_val}</div>
            </div>
        """

    html += '</div>'
    html += '<p style="text-align:center; font-size:0.7rem; color:#ccc; margin-top:15px;">※スプレッドシート「堀籠天気メモ」から自動取得中だぉ</p>'
    
    st.markdown(html, unsafe_allow_html=True)

except Exception as e:
    st.error(f"エラーだぉ、こーじ！：{e}")
