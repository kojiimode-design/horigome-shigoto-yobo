import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

st.set_page_config(page_title="堀籠天気仕事予報", layout="wide")
st.title("堀籠天気仕事予報")

# 認証設定
try:
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    # 住所（ID）を直接指定！これで404を撃退するぉ！
    spreadsheet_id = "1BU703DpWDUhF7nCOu_P38F3O2VxaWmVoLbcdY6klFj0"

    # Secretsから認証情報を取得（ここはgspreadの箱を使うぉ）
    creds_dict = {
        "type": st.secrets["gspread_credentials"]["type"],
        "project_id": st.secrets["gspread_credentials"]["project_id"],
        "private_key_id": st.secrets["gspread_credentials"]["private_key_id"],
        "private_key": st.secrets["gspread_credentials"]["private_key"].replace('\\n', '\n'),
        "client_email": st.secrets["gspread_credentials"]["client_email"],
        "token_uri": st.secrets["gspread_credentials"]["token_uri"],
        "auth_uri": st.secrets["gspread_credentials"]["auth_uri"],
    }

    credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(credentials)

    # スプレッドシート読み込み
    sh = gc.open_by_key(spreadsheet_id)
    worksheet = sh.get_worksheet(0)
    
    data = worksheet.get_all_values()
    if data:
        df = pd.DataFrame(data[1:], columns=data[0])
        st.dataframe(df, use_container_width=True)
    else:
        st.write("シートにデータがないぉ！")

except Exception as e:
    st.error(f"エラーだぉ：{e}")
