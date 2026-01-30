import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import requests

# ページ設定
st.set_page_config(page_title="堀籠天気仕事予報", layout="centered")

# デザイン設定（1枚目の Colab デザインを完全再現）
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

# 1. 天気予報と気温を「どんな形でも」取得する
@st.cache_data(ttl=600)
def get_weather_info():
    try:
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
        res = requests.get(url).json()
        
        # 週間予報から抽出（一番安定しているエリア）
        w_series = res[1]["timeSeries"]
        raw_weathers = w_series[0]["areas"][0]["weathers"]
        raw_max = w_series[1]["areas"][0]["tempsMax"]
        raw_min = w_series[1]["areas"][0]["tempsMin"]
        
        # 取得したデータを使いやすい形に整える
        weathers = []
        temps = []
        for i in range(10): # 最大10日分
            # 天気
            w = raw_weathers[i] if i < len(raw_weathers) else "不明"
            weathers.append(w)
            # 気温（週間予報は明日から始まることが多いので、よしなに調整）
            mx = raw_max[i] if i < len(raw_max) and raw_max[i] != "" else "--"
            mn = raw_min[i] if i < len(raw_min) and raw_min[i] != "" else "--"
            temps.append(f"<span style='color:#ff6b6b'>{mx}</span> / <span style='color:#4a90e2'>{mn}</span> ℃")
            
        return weathers, temps
    except:
        return ["不明"]*10, ["-- / -- ℃"]*10

weathers, temps = get_weather_info()

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
        # スプレッドシートの日付（例: 2026-2-2 -> 2/2）
        d_val = str(row.get('日付', '')).replace("2026-", "").replace("-", "/")
        j_val = str(row.get('行程', ' '))
        
        # 天気と気温をスプレッドシートの行に合わせて取得
        # ※週間予報は「明日」から始まることが多いので、i=0（2/2）なら予報の0番目を出す
        w_text = weathers[i] if i < len(weathers) else " "
        t_text = temps[i] if i < len(temps) else "-- / -- ℃"
        
        icon = "☀️" if "晴" in w_text else "☔" if "雨" in w_text else "❄️" if "雪" in w_text else "☁️"

        st.markdown(f"""
            <div class="weather-card">
                <div class="date-text">{d_val}</div>
                <div class="weather-content">
                    <div class="weather-main"><span>{icon}</span>&nbsp;{w_text[:12]}</div>
                    <div class="temp-text">{t_text}</div>
                </div>
                <div class="job-capsule">{j_val}</div>
            </div>
        """, unsafe_allow_html=True)
except Exception as e:
    st.error(f"読み込みエラー：{e}")
