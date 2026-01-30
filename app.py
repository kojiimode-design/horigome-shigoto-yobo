import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="堀籠天気仕事予報", layout="wide")

# 岩見沢の天気予報を取得する関数
def get_weather():
    try:
        # 気象庁のAPI（岩見沢を含む空知地方の予報）
        url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
        response = requests.get(url)
        data = response.json()
        
        # 岩見沢周辺の予報を抽出
        area_data = data[0]["timeSeries"][0]["areas"][0]
        weather_list = area_data["weathers"]
        
        return weather_list[0], weather_list[1] # 今日と明日の天気
    except:
        return "取得失敗だぉ", "取得失敗だぉ"

# 画面表示
st.title("堀籠天気仕事予報 🌤️")

# 天気予報エリア
today_w, tomorrow_w = get_weather()
col1, col2 = st.columns(2)
with col1:
    st.metric("今日の岩見沢", today_w)
with col2:
    st.metric("明日の岩見沢", tomorrow_w)

st.divider()

# スプレッドシート読み込み
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    creds_info = {
        "type": st.secrets["gspread_credentials"]["type"],
        "project_id": st.secrets["gspread_credentials"]["project_id"],
        "private_key_id": st.secrets["gspread_credentials"]["private_key_id"],
        "private_key": st.secrets["gspread_credentials"]["private_key"],
        "client_email": st.secrets["gspread_credentials"]["client_email"],
        "token_uri": st.secrets["gspread_credentials"]["token_uri"],
        "auth_uri": st.secrets["gspread_credentials"]["auth_uri"],
    }

    credentials = Credentials.from_service_account_info(creds_info, scopes=scope)
    gc = gspread.authorize(credentials)

    spreadsheet_id = st.secrets["spreadsheet_id"]
    sh = gc.open_by_key(spreadsheet_id)
    worksheet = sh.get_worksheet(0)
    
    data = worksheet.get_all_values()
    if data:
        df = pd.DataFrame(data[1:], columns=data[0])
        st.write("### 📝 仕事メモ")
        st.dataframe(df, use_container_width=True)
    else:
        st.write("シートにデータがないぉ！")

except Exception as e:
    st.error(f"エラーだぉ：{e}")
