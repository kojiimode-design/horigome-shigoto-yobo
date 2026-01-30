iimport streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import requests
from datetime import datetime

# --- ページ設定 ---
st.set_page_config(page_title="堀籠天気仕事予報", layout="centered")

# --- 1. 天気と気温を読み込む（週間予報メイン） ---
@st.cache_data(ttl=3600)
def get_weather_data():
    weather_map = {}
    try:
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
        res = requests.get(url).json()
        
        # 週間予報（res[1]）から取得
        ts_week = res[1]["timeSeries"]
        w_times = ts_week[0]["timeDefines"]
        w_weathers = ts_week[0]["areas"][0]["weathers"]
        # 気温は2番目のtimeSeriesに入ってるぉ
        w_max = ts_week[1]["areas"][0].get("tempsMax", ["--"] * len(w_times))
        w_min = ts_week[1]["areas"][0].get("tempsMin", ["--"] * len(w_times))
        
        for i in range(len(w_times)):
            dt = datetime.fromisoformat(w_times[i])
            date_key = f"{dt.year}-{dt.month}-{dt.day}"
            weather_map[date_key] = {
                "w": w_weathers[i].replace('　', ' '),
                "ma": w_max[i] if w_max[i] != "" else "--",
                "mi": w_min[i] if w_min[i] != "" else "--"
            }
    except: pass
    return weather_map

weather_dict = get_weather_data()

# --- 2. スプレッドシート読み込み ---
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds_info = st.secrets["gspread_credentials"]
    credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(st.secrets["spreadsheet_id"])
    worksheet = sh.get_worksheet(0)
    all_rows = worksheet.get_all_records()[:7] # 7日分

    # --- 3. デザインとHTMLを1つの変数にまとめるぉ！ ---
    # ここにColabのCSSを詰め込んだぉ
    html_content = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
        .colab-style-card {
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            border-radius: 30px;
            padding: 30px 20px;
            font-family: 'Noto Sans JP', sans-serif;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            max-width: 550px;
            margin: auto;
            color: #444;
        }
        .day-row {
            display: flex; align-items: center; justify-content: space-between;
            padding: 12px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.4);
        }
        .day-row:last-child { border-bottom: none; }
        .date-col { width: 100px; font-weight: bold; font-size: 0.95rem; }
        .sat { color: #4a90e2; } .sun { color: #ff6b6b; }
        .weather-col { flex-grow: 1; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .temp-max { color: #ff6b6b; font-weight: bold; }
        .temp-min { color: #4a90e2; font-weight: bold; }
        .job-col {
            background: rgba(255, 255, 255, 0.8);
            padding: 6px 15px; border-radius: 12px;
            min-width: 150px; text-align: center;
            font-weight: bold; font-size: 0.85rem;
        }
    </style>
    <div class="colab-style-card">
        <h2 style="text-align: center; margin-bottom: 20px;">📋 堀籠天気仕事予報</h2>
    """

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

        w_info = weather_dict.get(match_key, {"w": "予報なし", "ma": "--", "mi": "--"})
        icon = "☀️" if "晴" in w_info["w"] else "☔" if "雨" in w_info["w"] else "❄️" if "雪" in w_info["w"] else "☁️"
        job_val = str(row.get('行程', row.get('仕事内容', ' ')))

        # 行を追加していくぉ
        html_content += f"""
        <div class="day-row">
            <div class="date-col {wd_class}">{display_date}</div>
            <div class="weather-col">
                <span>{icon}</span>
                <span style="font-size:0.75rem; width:60px;">{w_info['w'][:5]}</span>
                <span class="temp-max">{w_info['ma']}</span> / <span class="temp-min">{w_info['mi']}</span>
            </div>
            <div class="job-col">{job_val}</div>
        </div>
        """

    html_content += "</div>" # カードを閉じる
    
    # ここが一番大事！st.markdownで一気に表示だぉ！
    st.markdown(html_content, unsafe_allow_html=True)

except Exception as e:
    st.error(f"エラーだぉ、こーじ！：{e}")
