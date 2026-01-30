import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import requests
from datetime import datetime

# --- 基本設定だぉ ---
st.set_page_config(page_title="堀籠天気仕事予報", layout="centered")

# --- デザイン設定（こーじのレイアウトを完全固定だぉ！） ---
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

# --- 1. 天気データを「日付をキーにした辞書」で取得（これが1ミリも狂わないコツだぉ！） ---
@st.cache_data(ttl=3600)
def get_weather_dict():
    weather_map = {}
    try:
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
        res = requests.get(url).json()
        
        # 週間予報の方（res[1]）から取得するぉ
        ts_week = res[1]["timeSeries"]
        times = ts_week[0]["timeDefines"]
        weathers = ts_week[0]["areas"][0]["weathers"]
        
        # 気温（最高・最低）
        max_temps = ts_week[1]["areas"][0].get("tempsMax", ["--"] * len(times))
        min_temps = ts_week[1]["areas"][0].get("tempsMin", ["--"] * len(times))
        
        for i in range(len(times)):
            dt = datetime.fromisoformat(times[i])
            # スプレッドシートの「2026-2-2」形式に合わせたキーを作るぉ
            date_key = f"{dt.year}-{dt.month}-{dt.day}"
            weather_map[date_key] = {
                "weather": weathers[i],
                "max": max_temps[i] if max_temps[i] != "" else "--",
                "min": min_temps[i] if min_temps[i] != "" else "--"
            }
    except Exception as e:
        # エラーが出てもアプリを止めない工夫だぉ
        pass
    return weather_map

weather_dict = get_weather_dict()

# --- 2. スプレッドシート取得と表示 ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_info = st.secrets["gspread_credentials"]
    credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(st.secrets["spreadsheet_id"])
    worksheet = sh.get_worksheet(0)
    
    # 週間予報なので直近7日分だけ出すぉ！
    all_rows = worksheet.get_all_records()[:7] 
    
    for row in all_rows:
        # スプレッドシートの日付を文字列として取得
        date_val = str(row.get('日付', '')).strip()
        
        # 表示用の形式（例：2/2）
        try:
            dt_obj = pd.to_datetime(date_val)
            display_date = f"{dt_obj.month}/{dt_obj.day}"
            # マッチング用のキー（2026-2-2）
            match_key = f"{dt_obj.year}-{dt_obj.month}-{dt_obj.day}"
        except:
            display_date = date_val
            match_key = date_val

        # 天気辞書から「日付」で検索！これが1ミリも狂わない秘訣だぉ！
        w_info = weather_dict.get(match_key, {"weather": "予報なし", "max": "--", "min": "--"})
        w_text = w_info["weather"]
        
        # アイコン判定
        icon = "☀️" if "晴" in w_text else "☔" if "雨" in w_text else "❄️" if "雪" in w_text else "☁️"
        
        # こーじの指定した「行程」を表示（なければ「仕事内容」を探すぉ）
        job_val = str(row.get('行程', row.get('仕事内容', '未定')))

        st.markdown(f"""
            <div class="weather-card">
                <div class="date-text">{display_date}</div>
                <div class="weather-content">
                    <div class="weather-main"><span>{icon}</span>&nbsp;{w_text[:10]}</div>
                    <div class="temp-text"><span style='color:#ff6b6b'>{w_info['max']}</span> / <span style='color:#4a90e2'>{w_info['min']}</span> ℃</div>
                </div>
                <div class="job-capsule">{job_val}</div>
            </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"読み込みエラーだぉ、こーじ！：{e}")
