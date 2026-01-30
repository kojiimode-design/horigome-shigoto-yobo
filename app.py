import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- 気象データ取得ロジック ---
def get_weather_data():
    # 岩見沢/空知地方のコード
    url = "https://www.jma.go.jp/bosai/forecast/data/forecast/016000.json"
    res = requests.get(url).json()
    
    weather_map = {}
    
    # 1. 直近の予報（今日・明日・明後日）
    area_data = res[0]['timeSeries'][0]
    time_defines = area_data['timeDefines']
    weathers = area_data['areas'][0]['weathers'] # 岩見沢（空知）
    
    # 2. 気温（直近）
    temp_data = res[0]['timeSeries'][2]['areas'][0]['temps']
    
    for i, time_str in enumerate(time_defines):
        date_key = datetime.fromisoformat(time_str).strftime('%Y-%m-%d')
        weather_map[date_key] = {
            "weather": weathers[i],
            "temp": temp_data[i] if i < len(temp_data) else "--"
        }

    # 3. 週間予報（3日目以降）
    week_data = res[1]['timeSeries'][0]
    week_times = week_data['timeDefines']
    week_weathers = week_data['areas'][0]['weathers']
    
    for i, time_str in enumerate(week_times):
        date_key = datetime.fromisoformat(time_str).strftime('%Y-%m-%d')
        # すでに直近予報がある場合は上書きしない（精度の高い方を優先）
        if date_key not in weather_map:
            weather_map[date_key] = {
                "weather": week_weathers[i],
                "temp": "--" # 週間予報の気温取得ロジックは別途追加可能
            }
            
    return weather_map

# --- メイン処理 ---
def main():
    st.set_page_config(page_title="堀籠天気仕事予報", layout="wide")
    
    # スプレッドシート読み込み（既存のロジックを想定）
    # df = load_gsheet_data() 
    
    weather_dict = get_weather_data()
    
    # スプレッドシートの日付（2026-2-2形式）を変換してマッチング
    for index, row in df.iterrows():
        # 日付フォーマットを統一 (例: '2026-02-02')
        target_date = pd.to_datetime(row['日付']).strftime('%Y-%m-%d')
        
        weather_info = weather_dict.get(target_date, {"weather": "取得中...", "temp": "--"})
        
        # ここでパステルカラーのカードを描画
        # render_card(row['日付'], weather_info['weather'], weather_info['temp'], row['仕事内容'])
