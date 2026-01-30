import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="堀籠天気仕事予報", page_icon="📋")
st.title("📋 堀籠天気仕事予報")

# Secrets
SPREADSHEET_ID = st.secrets["spreadsheet_id"]
SERVICE_ACCOUNT_INFO = st.secrets["gspread_credentials"]

# Google認証
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO,
    scopes=SCOPES,
)

gc = gspread.authorize(creds)

# Sheets取得
sh = gc.open_by_key(SPREADSHEET_ID)
ws = sh.sheet1

# データ表示
data = ws.get_all_records()
st.dataframe(data)
