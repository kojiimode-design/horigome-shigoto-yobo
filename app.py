import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- 1. スプレッドシート読み込み（上から7行に制限） ---
def load_gsheet_data():
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_info(st.secrets["gspread_credentials"], scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
    data = sheet.get_all_records()
    # 最初の7日分だけ取得するぉ！
    return pd.DataFrame(data).head(7)

# --- 2. 気象データ取得（さらに安全にしたぉ） ---
def get_weather_data():
    url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
    weather_map = {}
    try:
        res = requests.get(url).json()
        # 3日分予報
        for ts in res[0]['timeSeries']:
            times = ts.get('timeDefines', [])
            for area in ts.get('areas', []):
                if "空知" in area['area']['name'] or "岩見沢" in area['area']['name']:
                    for i in range(len(times)):
                        dt = datetime.fromisoformat(times[i])
                        date_key = f"{dt.year}-{dt.month}-{dt.day}"
                        if date_key not in weather_map:
                            weather_map[date_key] = {"weather": "取得中", "temp": "--"}
                        if 'weathers' in area:
                            weather_map[date_key]["weather"] = area['weathers'][i].replace('　', ' ')
                        if 'temps' in area:
                            weather_map[date_key]["temp"] = f"{area['temps'][i]}℃"
        # 週間予報で補完
        ts_week = res[1]['timeSeries'][0]
        week_times = ts_week['timeDefines']
        week_area = ts_week['areas'][0]
        for i in range(len(week_times)):
            dt = datetime.fromisoformat(week_times[i])
            date_key = f"{dt.year}-{dt.month}-{dt.day}"
            if date_key not in weather_map or weather_map[date_key]["weather"] == "取得中":
                weather_map[date_key] = {
                    "weather": week_area['weathers'][i].replace('　', ' '),
                    "temp": "--"
                }
    except Exception:
        pass # エラー表示を消してスッキリさせるぉ
    return weather_map

# --- 3. メイン画面 ---
def main():
    st.set_page_config(page_title="堀籠天気仕事予報", layout="wide")

    # CSS: カードを横に並べてスクロールさせるぉ
    st.markdown("""
        <style>
        .main { background-color: #0e1117; }
        .stColumn {
            background: linear-gradient(135deg, #ffdee9 0%, #b5fffc 100%);
            border-radius: 12px; padding: 10px; margin: 5px;
            min-width: 140px; text-align: center; color: #444;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.2);
        }
        h3 { margin-bottom: 0px; font-size: 1.2rem; }
        .job-label { font-size: 0.8rem; font-weight: bold; margin-top: 5px; color: #333; }
        </style>
    """, unsafe_allow_html=True)

    st.title("☀️ 堀籠天気仕事予報 🛠️")

    try:
        df = load_gsheet_data()
        weather_dict = get_weather_data()
        job_col = '仕事内容' if '仕事内容' in df.columns else df.columns[1]

        # 1行に7個のカラムを並べるぉ
        cols = st.columns(len(df))

        for i, (index, row) in enumerate(df.iterrows()):
            raw_date = str(row['日付']).strip()
            # 2026-2-2形式に変換してマッチング
            try:
                dt_obj = pd.to_datetime(raw_date)
                match_key = f"{dt_obj.year}-{dt_obj.month}-{dt_obj.day}"
            except:
                match_key = raw_date

            w_info = weather_dict.get(match_key, {"weather": "予報なし", "temp": "--"})
            icon = "☀️" if "晴" in w_info['weather'] else "☔" if "雨" in w_info['weather'] else "☃️" if "雪" in w_info['weather'] else "☁️"

            with cols[i]:
                st.markdown(f"**{raw_date}**")
                st.write(f"### {icon}")
                st.caption(w_info['weather'][:10] + ("..." if len(w_info['weather']) > 10 else "")) # 長い天気名は切るぉ
                st.markdown(f"<span style='color:red; font-weight:bold;'>{w_info['temp']}</span>", unsafe_allow_html=True)
                st.markdown(f"<div class='job-label'>{row[job_col]}</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"エラーだぉ: {e}")

if __name__ == "__main__":
    main()
