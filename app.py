import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- 1. スプレッドシート読み込み設定 ---
def load_gsheet_data():
    # Secretsから認証情報を取得
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_info(st.secrets["gspread_credentials"], scopes=scopes)
    client = gspread.authorize(creds)
    
    # スプレッドシートを開く
    sheet = client.open_by_key(st.secrets["spreadsheet_id"]).sheet1
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# --- 2. 気象データ取得ロジック（日付マッチング強化版） ---
def get_weather_data():
    url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
    res = requests.get(url).json()
    
    weather_map = {}
    
    # 直近予報（今日・明日・明後日）
    try:
        area_data = res[0]['timeSeries'][0]
        time_defines = area_data['timeDefines']
        weathers = area_data['areas'][0]['weathers']
        # 気温データ（直近）
        temp_data = res[0]['timeSeries'][2]['areas'][0]['temps']
        
        for i, time_str in enumerate(time_defines):
            date_key = datetime.fromisoformat(time_str).strftime('%Y-%-m-%-d') # 2026-2-2 形式に合わせる
            weather_map[date_key] = {
                "weather": weathers[i].replace('　', ' '), # 全角スペース調整
                "temp": f"{temp_data[i]}℃" if i < len(temp_data) else "--"
            }

        # 週間予報
        week_data = res[1]['timeSeries'][0]
        week_times = week_data['timeDefines']
        week_weathers = week_data['areas'][0]['weathers']
        
        for i, time_str in enumerate(week_times):
            date_key = datetime.fromisoformat(time_str).strftime('%Y-%-m-%-d')
            if date_key not in weather_map:
                weather_map[date_key] = {
                    "weather": week_weathers[i],
                    "temp": "--"
                }
    except Exception as e:
        st.error(f"天気データの解析でエラーが出たぉ: {e}")
            
    return weather_map

# --- 3. メイン処理 ---
def main():
    st.set_page_config(page_title="堀籠天気仕事予報", layout="wide")

    # CSSでパステルカラーのグラデーションカードを再現
    st.markdown("""
        <style>
        .weather-card {
            background: linear-gradient(135deg, #ffdee9 0%, #b5fffc 100%);
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            color: #444;
        }
        .date-text { font-weight: bold; font-size: 1.2em; }
        .job-text { color: #333; margin-top: 10px; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    st.title("☀️ 堀籠天気仕事予報 🛠️")

    try:
        # データの読み込み
        df = load_gsheet_data()
        weather_dict = get_weather_data()

        # カラム表示
        cols = st.columns(len(df))

        for i, (index, row) in enumerate(df.iterrows()):
            # スプレッドシートの日付を文字列として取得
            date_str = str(row['日付']).strip() # "2026-2-2" 
            
            # 天気辞書から取得（なければ「不明」）
            weather_info = weather_dict.get(date_str, {"weather": "予報なし", "temp": "--"})

            with cols[i]:
                st.markdown(f"""
                    <div class="weather-card">
                        <div class="date-text">{date_str}</div>
                        <div style="font-size: 2em;">{"☀️" if "晴" in weather_info['weather'] else "☁️" if "曇" in weather_info['weather'] else "☔"}</div>
                        <div>{weather_info['weather']}</div>
                        <div style="color: #ff4b4b;">{weather_info['temp']}</div>
                        <hr>
                        <div class="job-text">📋 {row['仕事内容']}</div>
                    </div>
                """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"エラーが発生したぉ、こーじ！: {e}")

if __name__ == "__main__":
    main()
