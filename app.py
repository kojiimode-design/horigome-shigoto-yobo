import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

def main():
    st.title("📋 堀籠天気仕事予報")
    try:
        # Secretsの名前(gspread_credentials)に合わせるぉ！
        creds_info = st.secrets["gspread_credentials"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(st.secrets["spreadsheet_id"])
        data = sh.get_worksheet(0).get_all_values()
        st.table(data)
    except Exception as e:
        st.error(f"エラーだぉ：{e}")

if __name__ == "__main__":
    main()
