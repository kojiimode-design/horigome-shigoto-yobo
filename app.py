import streamlit as st
import gspread
import requests
from google.oauth2.service_account import Credentials
from datetime import datetime

# ======================
# 基本設定
# ======================
st.set_page_config(
    page_title="堀籠天気仕事予報",
    page_icon="📋",
    layout="centered"
)

st.title("📋 堀籠天気仕事予報だぉ")

# ======================
# Secrets 読み込み
# ======================
SPREADSHEET_ID = st.secrets["spreadsheet_id"]
SERVICE_ACCOUNT_INFO = st.secrets["gspread_credentials"]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO,
    scopes=SCOPES,
)

gc = gspread.authorize(creds)
ws = gc.open_by_key(SPREADSHEET_ID).sheet1

# ======================
# スプレッドシート取得
# ======================
records = ws.get_all_records()

if not records:
    st.warning("スプレッドシートが空だぉ")
    st.stop()

# 日付を datetime.date に変換
sheet_data = {}
for r in records:
    try:
        d = datetime.strptime(str(r["日付"]), "%Y-%m-%d").date()
        sheet_data[d] = r
    except:
        continue

# ======================
# 気象庁API取得
# ======================
url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
res = requests.get(url).json()

weather_by_date = {}

for block in res:
    for ts in block.get("timeSeries", []):
        time_defines = ts.get("timeDefines", [])
        areas = ts.get("areas", [])

        for area in areas:
            weathers = area.get("weathers", [])
            temps_max = area.get("tempsMax", [])
            temps_min = area.get("tempsMin", [])

            for i, t in enumerate(time_defines):
                try:
                    d = datetime.fromisoformat(t).date()
                except:
                    continue

                weather_by_date.setdefault(d, {})

                if i < len(weathers):
                    weather_by_date[d]["weather"] = weathers[i]
                if i < len(temps_max):
                    weather_by_date[d]["temp_max"] = temps_max[i]
                if i < len(temps_min):
                    weather_by_date[d]["temp_min"] = temps_min[i]

# ======================
# 表示（完全日付一致）
# ======================
for d in sorted(sheet_data.keys()):
    sheet_row = sheet_data[d]
    weather = weather_by_date.get(d, {})

    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #fceff9, #e0f7fa);
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 12px;
        ">
            <h4>{d}</h4>
            <p>📝 仕事：{sheet_row.get("仕事内容","")}</p>
            <p>☀ 天気：{weather.get("weather","不明")}</p>
            <p>🌡 気温：
                {weather.get("temp_min","-")}℃
                /
                {weather.get("temp_max","-")}℃
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
