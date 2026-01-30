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

# --- 2. 気象データ取得（超・安全版） ---
def get_weather_data():
    url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
    weather_map = {}
    try:
        res = requests.get(url).json()
        # 1. 直近予報 (今日・明日・明後日)
        for ts in res[0]['timeSeries']:
            times = ts.get('timeDefines', [])
            for area in ts.get('areas', []):
                # エリア名に「空知」が含まれるものを探す
                if "空知" in area['area']['name']:
                    for i in range(len(times)):
                        dt = datetime.fromisoformat(times[i])
                        date_key = f"{dt.year}-{dt.month}-{dt.day}"
                        if date_key not in weather_map:
                            weather_map[date_key] = {"weather": "不明", "temp": "--"}
                        # 天気
                        if 'weathers' in area and i < len(area['weathers']):
                            weather_map[date_key]["weather"] = area['weathers'][i].replace('　', ' ')
                        # 気温
                        if 'temps' in area and i < len(area['temps']):
                            weather_map[date_key]["temp"] = f"{area['temps'][i]}℃"

        # 2. 週間予報 (補完)
        ts_week = res[1]['timeSeries'][0]
        week_times = ts_week['timeDefines']
        week_area = ts_week['areas'][0]
        for i in range(len(week_times)):
            dt = datetime.fromisoformat(week_times[i])
            date_key = f"{dt.year}-{dt.month}-{dt.day}"
            if date_key not in weather_map or weather_map[date_key]["weather"] == "不明":
                weather_map[date_key] = {
                    "weather": week_area['weathers'][i].replace('　', ' '),
                    "temp": "--"
                }
    except Exception as e:
        st.error(f"天気取得エラーだぉ: {e}")
    return weather_map

# --- 3. メイン画面 ---
def main():
    st.set_page_config(page_title="堀籠天気仕事予報", layout="wide")

    # デザイン設定（標準コンテナ用）
    st.markdown("""
        <style>
        div[data-testid="column"] {
            background: linear-gradient(135deg, #ffdee9 0%, #b5fffc 100%);
            border-radius: 15px; padding: 15px; margin: 5px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
            min-width: 150px; text-align: center;
        }
        .date-label { font-size: 1.1em; font-weight: bold; color: #444; }
        .job-label { font-size: 0.9em; font-weight: bold; color: #333; margin-top: 10px; }
        </style>
    """, unsafe_allow_html=True)

    st.title("☀️ 堀籠天気仕事予報 🛠️")

    try:
        df = load_gsheet_data()
        weather_dict = get_weather_data()
        job_col = '仕事内容' if '仕事内容' in df.columns else df.columns[1]

        # 横スクロールを実現するためにコンテナを使用
        container = st.container()
        # カラムを非常に多く作成することで横並びを促す（最新のStreamlitなら自動でスクロール）
        cols = st.columns(len(df))

        for i, (index, row) in enumerate(df.iterrows()):
            # スプレッドシートの日付を正規化
            raw_date = str(row['日付']).strip()
            try:
                dt_obj = pd.to_datetime(raw_date)
                match_key = f"{dt_obj.year}-{dt_obj.month}-{dt_obj.day}"
            except:
                match_key = raw_date

            w_info = weather_dict.get(match_key, {"weather": "予報なし", "temp": "--"})
            icon = "☀️" if "晴" in w_info['weather'] else "☔" if "雨" in w_info['weather'] else "☃️" if "雪" in w_info['weather'] else "☁️"

            with cols[i]:
                st.markdown(f"<div class='date-label'>{raw_date}</div>", unsafe_allow_html=True)
                st.write(f"### {icon}")
                st.caption(w_info['weather'])
                st.markdown(f"<span style='color:red; font-weight:bold;'>{w_info['temp']}</span>", unsafe_allow_html=True)
                st.markdown(f"<div class='job-label'>{row[job_col]}</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"エラーだぉ、こーじ！: {e}")

if __name__ == "__main__":
    main()
