import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import requests
from datetime import datetime, timedelta

# ページ設定
st.set_page_config(page_title="堀籠天気仕事予報", layout="centered")

# デザイン設定
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    .weather-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border-radius: 20px; padding: 10px 18px; margin-bottom: 10px;
        display: flex; align-items: center; box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        font-family: 'Noto Sans JP', sans-serif; max-width: 480px; margin-left: auto; margin-right: auto;
    }
    .date-text { font-weight: bold; width: 65px; font-size: 0.9rem; color: #555; }
    .weather-content { flex-grow: 1; display: flex; flex-direction: column; align-items: center; padding: 0 10px; }
    .weather-main { display: flex; align-items: center; font-size: 0.8rem; color: #444; }
    .temp-text { font-size: 0.85rem; font-weight: bold; margin-top: 2px; }
    .job-capsule {
        background-color: rgba(255, 255, 255, 0.9); padding: 7px 15px; border-radius: 15px;
        font-weight: bold; color: #333; min-width: 140px; text-align: center; font-size: 0.85rem;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; color: #444;'>📋 堀籠天気仕事予報</h2>", unsafe_allow_html=True)

# 1. 気象庁から全データを辞書形式で取得
@st.cache_data(ttl=600)
def get_weather_dict():
    try:
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
        res = requests.get(url).json()
        
        weather_map = {}
        
        # 週間予報の「日付」をキーにして天気と気温を保存
        weekly_data = res[1]["timeSeries"]
        times = weekly_data[0]["timeDefines"] # 日付リスト
        weathers = weekly_data[0]["areas"][0]["weathers"] # 天気リスト
        max_temps = weekly_data[1]["areas"][0]["tempsMax"] # 最高気温
        min_temps = weekly_data[1]["areas"][0]["tempsMin"] # 最低気温
        
        for i in range(len(times)):
            # 2026-02-02T00:00:00+09:00 の形から 2026-2-2 の形を作る
            dt = datetime.fromisoformat(times[i])
            date_key = f"{dt.year}-{dt.month}-{dt.day}"
            
            mx = max_temps[i] if i < len(max_temps) and max_temps[i] != "" else "--"
            mn = min_temps[i] if i < len(min_temps) and min_temps[i] != "" else "--"
            
            weather_map[date_key] = {
                "w": weathers[i],
                "t": f"<span style='color:#ff6b6b'>{mx}</span> / <span style='color:#4a90e2'>{mn}</span> ℃"
            }
        return weather_map
    except:
        return {}

w_dict = get_weather_dict()

# 2. スプレッドシート取得
try:
    creds_info = st.secrets["gspread_credentials"]
    credentials = Credentials.from_service_account_info(creds_info, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(st.secrets["spreadsheet_id"])
    worksheet = sh.get_worksheet(0)
    all_rows = worksheet.get_all_records()
    
    # 3. 表示
    for row in all_rows:
        date_raw = str(row.get('日付', '')) # 2026-2-2
        job_val = str(row.get('行程', ' '))
        
        # スプレッドシートの日付を使って天気データを検索
        info = w_dict.get(date_raw, {"w": "不明", "t": "-- / -- ℃"})
        w_text = info["w"]
        t_text = info["t"]
        
        display_date = date_raw.replace("2026-", "").replace("-", "/")
        icon = "☀️" if "晴" in w_text else "☔" if "雨" in w_text else "❄️" if "雪" in w_text else "☁️"

        st.markdown(f"""
            <div class="weather-card">
                <div class="date-text">{display_date}</div>
                <div class="weather-content">
                    <div class="weather-main"><span>{icon}</span>&nbsp;{w_text[:12]}</div>
                    <div class="temp-text">{t_text}</div>
                </div>
                <div class="job-capsule">{job_val}</div>
            </div>
        """, unsafe_allow_html=True)
except Exception as e:
    st.error(f"エラー：{e}")
