import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- 1. スプレッドシート読み込み ---
def load_gsheet_data():
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_info(st.secrets["gspread_credentials"], scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# --- 2. 気象データ取得（超安定版） ---
def get_weather_data():
    url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
    res = requests.get(url).json()
    weather_map = {}

    try:
        # 1. 直近予報の解析
        for ts in res[0]['timeSeries']:
            times = ts.get('timeDefines', [])
            for area in ts.get('areas', []):
                # 岩見沢（空知地方）のデータを探す
                if area['area']['name'] in ["空知地方", "岩見沢"]:
                    for i in range(len(times)):
                        dt = datetime.fromisoformat(times[i])
                        date_key = f"{dt.year}-{dt.month}-{dt.day}"
                        
                        if date_key not in weather_map:
                            weather_map[date_key] = {"weather": "--", "temp": "--"}
                        
                        if 'weathers' in area:
                            weather_map[date_key]["weather"] = area['weathers'][i].replace('　', ' ')
                        if 'temps' in area:
                            weather_map[date_key]["temp"] = f"{area['temps'][i]}℃"

        # 2. 週間予報の解析（3日目以降を補完）
        ts_week = res[1]['timeSeries'][0]
        week_times = ts_week['timeDefines']
        week_area = ts_week['areas'][0] # 週間は先頭が空知
        for i in range(len(week_times)):
            dt = datetime.fromisoformat(week_times[i])
            date_key = f"{dt.year}-{dt.month}-{dt.day}"
            if date_key not in weather_map or weather_map[date_key]["weather"] == "--":
                weather_map[date_key] = {
                    "weather": week_area['weathers'][i],
                    "temp": "--"
                }
    except Exception as e:
        st.error(f"天気データの解析でエラーが出たぉ: {e}")
    return weather_map

# --- 3. メイン画面 ---
def main():
    st.set_page_config(page_title="堀籠天気仕事予報", layout="wide")

    # CSS: カードの幅を固定して、綺麗に並ぶように調整
    st.markdown("""
        <style>
        .weather-card {
            background: linear-gradient(135deg, #ffdee9 0%, #b5fffc 100%);
            border-radius: 12px; padding: 10px; margin: 5px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: #444;
            min-width: 120px; text-align: center;
        }
        .date-text { font-weight: bold; font-size: 0.9em; border-bottom: 1px solid #fff; margin-bottom: 5px; }
        .job-text { color: #333; margin-top: 8px; font-weight: bold; font-size: 0.85em; background: rgba(255,255,255,0.3); border-radius: 5px; }
        </style>
    """, unsafe_allow_html=True)

    st.title("☀️ 堀籠天気仕事予報 🛠️")

    try:
        df = load_gsheet_data()
        weather_dict = get_weather_data()

        # 横スクロールできるように、たくさんのカラムを作成
        cols = st.columns(len(df))

        # スプレッドシートのカラム名を取得
        job_col = '仕事内容' if '仕事内容' in df.columns else df.columns[1]

        for i, (index, row) in enumerate(df.iterrows()):
            # スプレッドシートの日付（2026-2-2）をそのまま文字列として扱う
            date_str = str(row['日付']).strip()
            
            # 念のため「2026-02-02」のようなゼロ付きも「2026-2-2」に変換して照合
            try:
                dt_obj = pd.to_datetime(date_str)
                match_key = f"{dt_obj.year}-{dt_obj.month}-{dt_obj.day}"
            except:
                match_key = date_str

            weather_info = weather_dict.get(match_key, {"weather": "予報なし", "temp": "--"})

            with cols[i]:
                w_text = weather_info['weather']
                icon = "☀️" if "晴" in w_text else "☔" if "雨" in w_text else "☃️" if "雪" in w_text else "☁️"
                
                st.markdown(f"""
                    <div class="weather-card">
                        <div class="date-text">{date_str}</div>
                        <div style="font-size: 1.2em;">{icon}</div>
                        <div style="font-size: 0.7em; height: 30px;">{w_text}</div>
                        <div style="color: #ff4b4b; font-weight: bold; font-size: 0.9em;">{weather_info['temp']}</div>
                        <div class="job-text">{row[job_col]}</div>
                    </div>
                """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"エラーだぉ、こーじ！: {e}")

if __name__ == "__main__":
    main()
