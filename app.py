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

# --- 2. 気象データ取得（エラー回避強化版） ---
def get_weather_data():
    url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
    weather_map = {}
    try:
        res = requests.get(url).json()
        # 直近予報の解析
        for ts in res[0]['timeSeries']:
            times = ts.get('timeDefines', [])
            for area in ts.get('areas', []):
                # エリア名が「空知地方」や「岩見沢」を含むかチェック
                if any(name in area['area']['name'] for name in ["空知", "岩見沢"]):
                    for i in range(len(times)):
                        dt = datetime.fromisoformat(times[i])
                        date_key = f"{dt.year}-{dt.month}-{dt.day}"
                        if date_key not in weather_map:
                            weather_map[date_key] = {"weather": "--", "temp": "--"}
                        if 'weathers' in area:
                            weather_map[date_key]["weather"] = area['weathers'][i].replace('　', ' ')
                        if 'temps' in area:
                            weather_map[date_key]["temp"] = f"{area['temps'][i]}℃"
        # 週間予報の補完
        ts_week = res[1]['timeSeries'][0]
        week_times = ts_week['timeDefines']
        week_area = ts_week['areas'][0]
        for i in range(len(week_times)):
            dt = datetime.fromisoformat(week_times[i])
            date_key = f"{dt.year}-{dt.month}-{dt.day}"
            if date_key not in weather_map or weather_map[date_key]["weather"] == "--":
                weather_map[date_key] = {"weather": week_area['weathers'][i], "temp": "--"}
    except Exception as e:
        st.warning(f"天気データの解析でちょっとつまずいたぉ（{e}）。でも表示は続けるぉ！")
    return weather_map

# --- 3. メイン画面 ---
def main():
    st.set_page_config(page_title="堀籠天気仕事予報", layout="wide")

    # CSS: 横スクロールコンテナとカードのデザイン
    st.markdown("""
        <style>
        .scroll-container {
            display: flex;
            overflow-x: auto;
            white-space: nowrap;
            padding: 20px 0;
            gap: 15px;
            -webkit-overflow-scrolling: touch;
        }
        .weather-card {
            flex: 0 0 160px; /* カードの幅を固定 */
            background: linear-gradient(135deg, #ffdee9 0%, #b5fffc 100%);
            border-radius: 15px;
            padding: 15px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            color: #444;
            text-align: center;
            display: inline-block;
            vertical-align: top;
        }
        .date-text { font-weight: bold; font-size: 1em; border-bottom: 1px solid #fff; margin-bottom: 10px; padding-bottom: 5px; }
        .job-text { 
            margin-top: 10px; padding: 5px;
            background: rgba(255,255,255,0.4); 
            border-radius: 8px; font-weight: bold; font-size: 0.85em;
            white-space: normal; /* 仕事内容は折り返し許可 */
        }
        .temp-text { color: #ff4b4b; font-weight: bold; font-size: 1.1em; margin: 5px 0; }
        </style>
    """, unsafe_allow_html=True)

    st.title("☀️ 堀籠天気仕事予報 🛠️")

    try:
        df = load_gsheet_data()
        weather_dict = get_weather_data()
        job_col = '仕事内容' if '仕事内容' in df.columns else df.columns[1]

        # 横スクロールの開始
        html_content = '<div class="scroll-container">'

        for _, row in df.iterrows():
            date_str = str(row['日付']).strip()
            try:
                dt_obj = pd.to_datetime(date_str)
                match_key = f"{dt_obj.year}-{dt_obj.month}-{dt_obj.day}"
            except:
                match_key = date_str

            w_info = weather_dict.get(match_key, {"weather": "予報なし", "temp": "--"})
            icon = "☀️" if "晴" in w_info['weather'] else "☔" if "雨" in w_info['weather'] else "☃️" if "雪" in w_info['weather'] else "☁️"

            # カードをHTML文字列として追加
            html_content += f"""
                <div class="weather-card">
                    <div class="date-text">{date_str}</div>
                    <div style="font-size: 2em;">{icon}</div>
                    <div style="font-size: 0.75em; height: 40px; overflow: hidden;">{w_info['weather']}</div>
                    <div class="temp-text">{w_info['temp']}</div>
                    <div class="job-text">{row[job_col]}</div>
                </div>
            """

        html_content += '</div>' # コンテナ終了
        st.markdown(html_content, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"エラーだぉ、こーじ！: {e}")

if __name__ == "__main__":
    main()
