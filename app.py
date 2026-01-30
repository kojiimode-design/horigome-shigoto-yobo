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

# --- 2. 気象データ取得（階層構造を修正） ---
def get_weather_data():
    url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
    res = requests.get(url).json()
    weather_map = {}

    try:
        # --- 直近予報 ---
        # 階層をより確実に指定：[0]['timeSeries'][0] の中身
        ts0 = res[0]['timeSeries'][0]
        times = ts0['timeDefines']
        # 空知地方（岩見沢含む）のエリアデータを探す
        area_weathers = ts0['areas'][0]['weathers'] 
        
        # 気温データ
        ts2 = res[0]['timeSeries'][2]
        temp_list = ts2['areas'][0]['temps']

        for i in range(len(times)):
            dt = datetime.fromisoformat(times[i])
            # 2026-2-2 形式のキーを作成
            date_key = f"{dt.year}-{dt.month}-{dt.day}"
            weather_map[date_key] = {
                "weather": area_weathers[i].replace('　', ' '),
                "temp": f"{temp_list[i]}℃" if i < len(temp_list) else "--"
            }

        # --- 週間予報 ---
        ts_week = res[1]['timeSeries'][0]
        week_times = ts_week['timeDefines']
        week_weathers = ts_week['areas'][0]['weathers']
        
        for i in range(len(week_times)):
            dt = datetime.fromisoformat(week_times[i])
            date_key = f"{dt.year}-{dt.month}-{dt.day}"
            if date_key not in weather_map:
                weather_map[date_key] = {
                    "weather": week_weathers[i],
                    "temp": "--"
                }
    except Exception as e:
        st.error(f"天気データの解析でエラーが出たぉ: {e}")
    return weather_map

# --- 3. メイン画面 ---
def main():
    st.set_page_config(page_title="堀籠天気仕事予報", layout="wide")

    st.markdown("""
        <style>
        .weather-card {
            background: linear-gradient(135deg, #ffdee9 0%, #b5fffc 100%);
            border-radius: 15px; padding: 15px; margin: 5px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); color: #444; min-height: 200px;
        }
        .date-text { font-weight: bold; font-size: 1.1em; border-bottom: 1px solid #fff; }
        .job-text { color: #333; margin-top: 10px; font-weight: bold; font-size: 0.9em; }
        </style>
    """, unsafe_allow_html=True)

    st.title("☀️ 堀籠天気仕事予報 🛠️")

    try:
        df = load_gsheet_data()
        weather_dict = get_weather_data()

        # 横並びに表示（カラム数が多すぎると崩れるので調整）
        cols = st.columns(len(df) if len(df) > 0 else 1)

        # スプレッドシートのカラム名を確認（念のため）
        # '仕事内容' という名前がスプレッドシートにあるかチェック
        job_col = '仕事内容' if '仕事内容' in df.columns else df.columns[1] # なければ2列目を使用

        for i, (index, row) in enumerate(df.iterrows()):
            # 日付の型を柔軟に処理
            raw_date = str(row['日付']).strip()
            # 2026-02-02 などの形式を 2026-2-2 に正規化
            try:
                dt_obj = pd.to_datetime(raw_date)
                match_key = f"{dt_obj.year}-{dt_obj.month}-{dt_obj.day}"
            except:
                match_key = raw_date

            weather_info = weather_dict.get(match_key, {"weather": "予報なし", "temp": "--"})

            with cols[i]:
                icon = "☀️" if "晴" in weather_info['weather'] else "☔" if "雨" in weather_info['weather'] else "☁️"
                st.markdown(f"""
                    <div class="weather-card">
                        <div class="date-text">{match_key}</div>
                        <div style="font-size: 1.5em; margin: 10px 0;">{icon}</div>
                        <div style="font-size: 0.8em;">{weather_info['weather']}</div>
                        <div style="color: #ff4b4b; font-weight: bold;">{weather_info['temp']}</div>
                        <div class="job-text">📋 {row[job_col]}</div>
                    </div>
                """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"エラーが発生したぉ、こーじ！: {e}")

if __name__ == "__main__":
    main()
