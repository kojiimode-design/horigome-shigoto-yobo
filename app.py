import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import requests
from datetime import datetime

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

# 1. 気象庁のデータを取得（リスト形式で順番に保持）
@st.cache_data(ttl=600)
def get_weather_list():
    try:
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
        res = requests.get(url).json()
        
        # 週間予報（res[1]）からデータを抜く
        w_series = res[1]["timeSeries"]
        w_list = w_series[0]["areas"][0]["weathers"] # 天気
        max_list = w_series[1]["areas"][0]["tempsMax"] # 最高
        min_list = w_series[1]["areas"][0]["tempsMin"] # 最低
        
        # データをまとめる（予報がある分だけ）
        data_pool = []
        for i in range(len(w_list)):
            mx = max_list[i] if i < len(max_list) and max_list[i] != "" else "--"
            mn = min_list[i] if i < len(min_list) and min_list[i] != "" else "--"
            data_pool.append({
                "w": w_list[i],
                "t": f"<span style='color:#ff6b6b'>{mx}</span> / <span style='color:#4a90e2'>{mn}</span> ℃"
            })
        return data_pool
    except:
        return []

weather_pool = get_weather_list()

# 2. スプレッドシート取得
try:
    creds_info = st.secrets["gspread_credentials"]
    credentials = Credentials.from_service_account_info(creds_info, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(st.secrets["spreadsheet_id"])
    worksheet = sh.get_worksheet(0)
    all_rows = worksheet.get_all_records()
    
    # 3. 表示
    # 気象庁の週間予報は「明日（1/31）」から始まるので、シートの日付とのズレを調整
    # シートの 2/2 は今日から4日目、週間予報の「2番目(インデックス2)」あたり
    for i, row in enumerate(all_rows):
        d_raw = str(row.get('日付', ''))
        j_val = str(row.get('行程', ' '))
        
        # 表示用の日付（2/2 形式）
        d_disp = d_raw.replace("2026-", "").replace("-", "/")

        # --- 魔法のマッチング ---
        # シートの2/2、2/3...に合わせて、予報リストの 2番目、3番目...を順番に当てる
        # 週間予報の開始（明日）を 0 とすると、2/2 は 2番目になる計算
        w_info = {"w": "不明", "t": "-- / -- ℃"}
        if i < len(weather_pool):
            w_info = weather_pool[i]
        
        w_text = w_info["w"]
        t_text = w_info["t"]
        
        icon = "☀️" if "晴" in w_text else "☔" if "雨" in w_text else "❄️" if "雪" in w_text else "☁️"

        st.markdown(f"""
            <div class="weather-card">
                <div class="date-text">{d_disp}</div>
                <div class="weather-content">
                    <div class="weather-main"><span>{icon}</span>&nbsp;{w_text[:12]}</div>
                    <div class="temp-text">{t_text}</div>
                </div>
                <div class="job-capsule">{j_val}</div>
            </div>
        """, unsafe_allow_html=True)
except Exception as e:
    st.error(f"エラーが発生したぉ：{e}")
