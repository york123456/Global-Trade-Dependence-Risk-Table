#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OECD Global Trade GIS Dashboard
=================================
從 OECD SDMX API 抓取多年度進出口資料，
整理成互動式 Leaflet.js 世界地圖 (index.html)。

執行方式：
    python build_trade_dashboard.py           # 自動偵測（優先抓 OECD 真實資料）
    python build_trade_dashboard.py --demo    # 快速展示（使用內建參考資料）
    python build_trade_dashboard.py --real    # 強制使用 OECD API

輸出：index.html + data_cache/（API 快取）
"""

import os, json, time, hashlib, pickle, sys, math, random
from pathlib import Path
from IPython.utils.path import glob
import requests
import pandas as pd
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────────────────
# 設定區
# ─────────────────────────────────────────────────────────


YEARS       = [] #["2030"]
CACHE_DIR   = Path("data_cache")
OUTPUT_FILE = Path("index.html")
CACHE_DIR.mkdir(exist_ok=True)


def update_YEARS():
    global YEARS


    import datetime

    current_year = datetime.datetime.now().year -3

    # 產生帶有「年」字尾的字串列表
    year_str_list = [f"{current_year - i}" for i in range(3)]

    YEARS=year_str_list

    return YEARS





MAIN_COUNTRIES = []



def update_MAIN_COUNTRIES():

    global MAIN_COUNTRIES

    
    import requests
    
  
    url = os.environ.get('URL_TICKERS')

    tickers = requests.get(url)
    
    
    url =os.environ.get('URL_CONFIG')

    config = requests.get(url)
    
    
    
    #print('====1====')
    
    import csv
    import io
    
    # 使用 csv 模組解析
    f = io.StringIO(tickers.text.strip())
    reader = csv.DictReader(f)
    stock_list = list(reader)
    
    #print(stock_list[:5])
    
    #print('====2====')
    
    import ast
    import re
    #print('====3====')
    
    def extract_country_meta(text):
        # 1. 用正規表達式抓取 COUNTRY_META = { 到 下一個 } 之間的內容
        # dotall=True 讓 . 可以匹配換行符號
        match = re.search(r"COUNTRY_META\s*=\s*(\{.*?\n\s*\})", text, re.DOTALL)
        
        if not match:
            print("❌ 找不到 COUNTRY_META 區塊")
            return None
    
        dict_string = match.group(1)
    
        # 2. 清理掉 python 註解（避免 ast.literal_eval 解析失敗）
        # 移除以 # 開頭到行末的文字
        dict_string_clean = re.sub(r"#.*", "", dict_string)
    
        try:
            # 3. 將字串安全地轉換成 Python 字典物件
            country_dict = ast.literal_eval(dict_string_clean)
            return country_dict
        except Exception as e:
            print(f"❌ 字典解析失敗，錯誤原因: {e}")
            return None
    #print('====4====')
    
    # ─── 執行自動辨識 ───
    COUNTRY_META = extract_country_meta(config.text)
    #print('====5====')
    
    
    #print('COUNTRY_META',COUNTRY_META)
    
    
    # 定義一個查詢函式
    def get_iso3(country_name):
        # 先拿取該國家的內層字典，再從中拿取 iso3
        country_info = COUNTRY_META.get(country_name)
        if country_info:
            return country_info.get("iso3")
        return "找不到此國家"
    #print('====6====')
    
    data = stock_list
    
    # 找出 ... 為 25 的所有列
    #result = [row["國家"] for row in data if "國家" in row]
    #print(result)
    
    # 保持出現順序的去重
    unique_cities_ordered = list(dict.fromkeys(row["國家"] for row in data if "國家" in row))
    #print(unique_cities_ordered)
    # 輸出: ['台北', '台中']
    
    
    #print('====7====')
    
    
    MAIN_COUNTRIES=[]
    
    for country in unique_cities_ordered:
      MAIN_COUNTRIES.append(get_iso3(country)) 
    #print('====8====')
    
    #print('MAIN_COUNTRIES',MAIN_COUNTRIES)

    return MAIN_COUNTRIES
    
    
    




'''
MAIN_COUNTRIES = [
    "TWN","USA","CHN","JPN","KOR","DEU","GBR","FRA",
    "CAN","AUS","IND","BRA","MEX","ITA","NLD","ESP",
    "SGP","HKG","VNM","THA","IDN","MYS","PHL",
    "RUS","TUR","POL","CHE","SWE","NOR","DNK","FIN",
    "AUT","BEL","CZE","HUN","PRT","ROU","SVK","SVN",
    "GRC","ISR","NZL","ZAF","EGY","SAU","ARE","ARG","CHL","COL",
]
'''

# ─────────────────────────────────────────────────────────
# 產業代碼
# ─────────────────────────────────────────────────────────
PRODUCT_MAP = {
    "_T":              "總計",
    "CPA_2_1_A":       "農林漁業",
    "CPA_2_1_B":       "採礦業",
    "CPA_2_1_B06":     "石油天然氣",
    "CPA_2_1_C":       "製造業",
    "CPA_2_1_C10T12":  "食品飲料菸草",
    "CPA_2_1_C13T15":  "紡織服飾皮革",
    "CPA_2_1_C16T18":  "木材紙業印刷",
    "CPA_2_1_C19T23":  "化工燃料塑料",
    "CPA_2_1_C20":     "化學品",
    "CPA_2_1_C21":     "製藥",
    "CPA_2_1_C24_25":  "金屬製品",
    "CPA_2_1_C26":     "電腦電子光學",
    "CPA_2_1_C26ICT":  "ICT 製造",
    "CPA_2_1_C261":    "電子元件",
    "CPA_2_1_C263":    "通訊設備",
    "CPA_2_1_C27":     "電氣設備",
    "CPA_2_1_C28":     "機械設備",
    "CPA_2_1_C29":     "汽車",
    "CPA_2_1_C29_30":  "汽車與其他運輸",
    "CPA_2_1_C30":     "其他交通設備",
    "CPA_2_1_C303":    "航空航天",
    "CPA_2_1_C254":    "武器彈藥",
    "CPA_2_1_C325":    "醫療器材",
    "CPA_2_1_C31_32":  "家具及其他",
    "CPA_2_1_D35":     "電力燃氣",
    "CPA_2_1_EPA":     "能源產品",
    "CPA_2_1_HRD":     "高研發密集",
    "CPA_2_1_MHRD":    "中高研發密集",
    "CPA_2_1_MRD":     "中研發密集",
    "CPA_2_1_MLRD":    "中低研發密集",
    "CPA_2_1_LRD":     "低研發密集",
    "_X":              "未分類",
}

KEY_PRODUCTS = [
    "_T", "CPA_2_1_C", "CPA_2_1_C26", "CPA_2_1_C26ICT",
    "CPA_2_1_C261", "CPA_2_1_C29", "CPA_2_1_C20", "CPA_2_1_C21",
    "CPA_2_1_C28", "CPA_2_1_C27", "CPA_2_1_C303",
    "CPA_2_1_EPA", "CPA_2_1_B06",
    "CPA_2_1_HRD", "CPA_2_1_MHRD",
    "CPA_2_1_A", "CPA_2_1_C10T12",
]

# ─────────────────────────────────────────────────────────
# 國家元資料
# ─────────────────────────────────────────────────────────
COUNTRY_META = {
    "TWN":{"zh":"台灣",    "en":"Taiwan",            "lat":23.698,"lng":120.960,"region":"東亞"},
    "CHN":{"zh":"中國",    "en":"China",             "lat":35.861,"lng":104.195,"region":"東亞"},
    "JPN":{"zh":"日本",    "en":"Japan",             "lat":36.204,"lng":138.253,"region":"東亞"},
    "KOR":{"zh":"韓國",    "en":"South Korea",       "lat":35.908,"lng":127.767,"region":"東亞"},
    "HKG":{"zh":"香港",    "en":"Hong Kong",         "lat":22.302,"lng":114.177,"region":"東亞"},
    "SGP":{"zh":"新加坡",  "en":"Singapore",         "lat":1.352, "lng":103.820,"region":"東南亞"},
    "VNM":{"zh":"越南",    "en":"Vietnam",           "lat":14.058,"lng":108.277,"region":"東南亞"},
    "THA":{"zh":"泰國",    "en":"Thailand",          "lat":15.870,"lng":100.993,"region":"東南亞"},
    "IDN":{"zh":"印尼",    "en":"Indonesia",         "lat":-0.789,"lng":113.921,"region":"東南亞"},
    "MYS":{"zh":"馬來西亞","en":"Malaysia",          "lat":4.211, "lng":101.976,"region":"東南亞"},
    "PHL":{"zh":"菲律賓",  "en":"Philippines",       "lat":12.880,"lng":121.774,"region":"東南亞"},
    "IND":{"zh":"印度",    "en":"India",             "lat":20.594,"lng":78.963, "region":"南亞"},
    "USA":{"zh":"美國",    "en":"United States",     "lat":37.090,"lng":-95.713,"region":"北美"},
    "CAN":{"zh":"加拿大",  "en":"Canada",            "lat":56.130,"lng":-106.347,"region":"北美"},
    "MEX":{"zh":"墨西哥",  "en":"Mexico",            "lat":23.635,"lng":-102.553,"region":"北美"},
    "BRA":{"zh":"巴西",    "en":"Brazil",            "lat":-14.235,"lng":-51.925,"region":"南美"},
    "ARG":{"zh":"阿根廷",  "en":"Argentina",         "lat":-38.416,"lng":-63.617,"region":"南美"},
    "CHL":{"zh":"智利",    "en":"Chile",             "lat":-35.676,"lng":-71.543,"region":"南美"},
    "COL":{"zh":"哥倫比亞","en":"Colombia",          "lat":4.571, "lng":-74.297,"region":"南美"},
    "DEU":{"zh":"德國",    "en":"Germany",           "lat":51.166,"lng":10.452, "region":"歐洲"},
    "FRA":{"zh":"法國",    "en":"France",            "lat":46.228,"lng":2.214,  "region":"歐洲"},
    "GBR":{"zh":"英國",    "en":"United Kingdom",    "lat":55.378,"lng":-3.436, "region":"歐洲"},
    "ITA":{"zh":"義大利",  "en":"Italy",             "lat":41.872,"lng":12.568, "region":"歐洲"},
    "ESP":{"zh":"西班牙",  "en":"Spain",             "lat":40.463,"lng":-3.749, "region":"歐洲"},
    "NLD":{"zh":"荷蘭",    "en":"Netherlands",       "lat":52.133,"lng":5.291,  "region":"歐洲"},
    "BEL":{"zh":"比利時",  "en":"Belgium",           "lat":50.503,"lng":4.470,  "region":"歐洲"},
    "CHE":{"zh":"瑞士",    "en":"Switzerland",       "lat":46.818,"lng":8.228,  "region":"歐洲"},
    "AUT":{"zh":"奧地利",  "en":"Austria",           "lat":47.516,"lng":14.550, "region":"歐洲"},
    "POL":{"zh":"波蘭",    "en":"Poland",            "lat":51.920,"lng":19.145, "region":"歐洲"},
    "SWE":{"zh":"瑞典",    "en":"Sweden",            "lat":60.128,"lng":18.644, "region":"歐洲"},
    "NOR":{"zh":"挪威",    "en":"Norway",            "lat":60.472,"lng":8.469,  "region":"歐洲"},
    "DNK":{"zh":"丹麥",    "en":"Denmark",           "lat":56.263,"lng":9.502,  "region":"歐洲"},
    "FIN":{"zh":"芬蘭",    "en":"Finland",           "lat":61.924,"lng":25.748, "region":"歐洲"},
    "PRT":{"zh":"葡萄牙",  "en":"Portugal",          "lat":39.400,"lng":-8.224, "region":"歐洲"},
    "GRC":{"zh":"希臘",    "en":"Greece",            "lat":39.074,"lng":21.824, "region":"歐洲"},
    "CZE":{"zh":"捷克",    "en":"Czech Republic",    "lat":49.818,"lng":15.473, "region":"歐洲"},
    "HUN":{"zh":"匈牙利",  "en":"Hungary",           "lat":47.163,"lng":19.503, "region":"歐洲"},
    "ROU":{"zh":"羅馬尼亞","en":"Romania",           "lat":45.943,"lng":24.967, "region":"歐洲"},
    "SVK":{"zh":"斯洛伐克","en":"Slovakia",          "lat":48.669,"lng":19.699, "region":"歐洲"},
    "SVN":{"zh":"斯洛維尼亞","en":"Slovenia",        "lat":46.152,"lng":14.995, "region":"歐洲"},
    "RUS":{"zh":"俄羅斯",  "en":"Russia",            "lat":61.524,"lng":105.319,"region":"歐亞"},
    "TUR":{"zh":"土耳其",  "en":"Turkey",            "lat":38.964,"lng":35.244, "region":"歐亞"},
    "ISR":{"zh":"以色列",  "en":"Israel",            "lat":31.047,"lng":34.852, "region":"中東"},
    "SAU":{"zh":"沙烏地",  "en":"Saudi Arabia",      "lat":23.886,"lng":45.079, "region":"中東"},
    "ARE":{"zh":"阿聯酋",  "en":"UAE",               "lat":23.424,"lng":53.848, "region":"中東"},
    "EGY":{"zh":"埃及",    "en":"Egypt",             "lat":26.821,"lng":30.802, "region":"非洲"},
    "ZAF":{"zh":"南非",    "en":"South Africa",      "lat":-30.560,"lng":22.938,"region":"非洲"},
    "AUS":{"zh":"澳洲",    "en":"Australia",         "lat":-25.274,"lng":133.775,"region":"大洋洲"},
    "NZL":{"zh":"紐西蘭",  "en":"New Zealand",       "lat":-40.901,"lng":172.885,"region":"大洋洲"},
}

ISO3_TO_GEOJSON = {
    "TWN":"Taiwan","CHN":"China","JPN":"Japan","KOR":"South Korea",
    "HKG":"Hong Kong","SGP":"Singapore","VNM":"Vietnam","THA":"Thailand",
    "IDN":"Indonesia","MYS":"Malaysia","PHL":"Philippines","IND":"India",
    "USA":"United States of America","CAN":"Canada","MEX":"Mexico",
    "BRA":"Brazil","ARG":"Argentina","CHL":"Chile","COL":"Colombia",
    "DEU":"Germany","FRA":"France","GBR":"United Kingdom","ITA":"Italy",
    "ESP":"Spain","NLD":"Netherlands","BEL":"Belgium","CHE":"Switzerland",
    "AUT":"Austria","POL":"Poland","SWE":"Sweden","NOR":"Norway",
    "DNK":"Denmark","FIN":"Finland","PRT":"Portugal","GRC":"Greece",
    "CZE":"Czech Republic","HUN":"Hungary","ROU":"Romania",
    "SVK":"Slovakia","SVN":"Slovenia","RUS":"Russia","TUR":"Turkey",
    "ISR":"Israel","SAU":"Saudi Arabia","ARE":"United Arab Emirates",
    "EGY":"Egypt","ZAF":"South Africa","AUS":"Australia","NZL":"New Zealand",
}

# ─────────────────────────────────────────────────────────
# DEMO 資料生成（基於真實量級的參考資料）
# ─────────────────────────────────────────────────────────

def build_demo_data() -> pd.DataFrame:
    """
    使用參考真實 OECD BTIGE 資料量級的模擬資料，
    讓 index.html 可以立即展示完整功能。
    參考來源：OECD BTIGE 2020 公開摘要報告。
    """
    print("  [Demo 模式] 使用內建參考資料（真實量級）")
    random.seed(42)

    # 各國出口總量基準（百萬美元，2020 參考值）
    base_exp = {
        "CHN":2591000,"USA":1432000,"DEU":1380000,"JPN":641000,
        "KOR":512000, "NLD":674000, "HKG":549000, "FRA":488000,
        "ITA":496000, "GBR":405000, "BEL":408000, "CAN":390000,
        "SGP":362000, "MEX":417000, "RUS":337000, "CHE":310000,
        "AUS":249000, "IND":276000, "ESP":280000, "POL":259000,
        "TWN":342000, "SWE":164000, "AUT":157000, "CZE":193000,
        "THA":214000, "VNM":283000, "MYS":230000, "IDN":164000,
        "TUR":169000, "BRA":209000, "DNK":114000, "SAU":176000,
        "NOR":103000, "ARE":323000, "FIN":72000,  "HUN":112000,
        "ARG":54000,  "NZL":39000,  "ZAF":85000,  "ISR":63000,
        "PHL":71000,  "EGY":26000,  "CHL":73000,  "COL":32000,
        "PRT":62000,  "GRC":37000,  "SVN":33000,  "ROU":71000,
        "SVK":88000,  "BEL":408000,
    }
    base_imp = {k: int(v * random.uniform(0.7, 1.3)) for k,v in base_exp.items()}
    # 修正已知逆差國
    for c in ["USA","GBR","FRA","IND"]:
        if c in base_imp: base_imp[c] = int(base_exp.get(c,100000) * 1.4)

    # 各國主要對口貿易夥伴（出口）
    partner_weights = {
        "TWN":{"CHN":0.30,"USA":0.15,"HKG":0.14,"JPN":0.07,"SGP":0.06,
               "KOR":0.05,"DEU":0.03,"VNM":0.04,"NLD":0.03,"AUS":0.02},
        "CHN":{"USA":0.18,"HKG":0.11,"JPN":0.06,"KOR":0.05,"DEU":0.04,
               "VNM":0.05,"NLD":0.04,"GBR":0.03,"IND":0.03,"AUS":0.05},
        "USA":{"CAN":0.18,"MEX":0.16,"CHN":0.09,"JPN":0.05,"GBR":0.05,
               "DEU":0.04,"KOR":0.04,"NLD":0.04,"FRA":0.03,"SGP":0.02},
        "DEU":{"USA":0.09,"CHN":0.08,"FRA":0.08,"NLD":0.07,"GBR":0.07,
               "POL":0.06,"ITA":0.05,"AUT":0.05,"BEL":0.05,"CHE":0.04},
        "JPN":{"CHN":0.22,"USA":0.19,"KOR":0.07,"TWN":0.07,"HKG":0.05,
               "THA":0.05,"DEU":0.04,"SGP":0.03,"AUS":0.04,"VNM":0.03},
        "KOR":{"CHN":0.26,"USA":0.15,"VNM":0.10,"HKG":0.08,"JPN":0.05,
               "TWN":0.04,"IND":0.03,"AUS":0.03,"DEU":0.03,"SGP":0.03},
        "GBR":{"USA":0.15,"DEU":0.11,"FRA":0.09,"NLD":0.08,"IRL":0.06,
               "CHN":0.05,"BEL":0.05,"ESP":0.04,"ITA":0.04,"AUS":0.02},
        "FRA":{"DEU":0.16,"USA":0.09,"GBR":0.09,"ITA":0.08,"ESP":0.07,
               "BEL":0.07,"CHN":0.05,"NLD":0.06,"CHE":0.04,"POL":0.03},
    }
    # 其他國家用通用模板
    default_partners = {
        "USA":0.15,"CHN":0.12,"DEU":0.09,"JPN":0.07,"GBR":0.06,
        "FRA":0.05,"KOR":0.05,"ITA":0.04,"NLD":0.04,"AUS":0.03,
    }

    # 各國產業出口比例
    sector_weights = {
        "TWN":{"CPA_2_1_C26":0.35,"CPA_2_1_C261":0.22,"CPA_2_1_C26ICT":0.18,
               "CPA_2_1_C28":0.08,"CPA_2_1_C27":0.06,"CPA_2_1_MHRD":0.20,
               "CPA_2_1_HRD":0.15,"CPA_2_1_C21":0.04,"CPA_2_1_C":0.90},
        "CHN":{"CPA_2_1_C":0.92,"CPA_2_1_C26":0.18,"CPA_2_1_C13T15":0.08,
               "CPA_2_1_C24_25":0.10,"CPA_2_1_C28":0.09,"CPA_2_1_C29":0.06,
               "CPA_2_1_MLRD":0.25,"CPA_2_1_MHRD":0.20,"CPA_2_1_C10T12":0.05},
        "DEU":{"CPA_2_1_C29":0.18,"CPA_2_1_C28":0.14,"CPA_2_1_C":0.88,
               "CPA_2_1_C20":0.09,"CPA_2_1_C26":0.08,"CPA_2_1_C27":0.07,
               "CPA_2_1_MHRD":0.30,"CPA_2_1_HRD":0.12,"CPA_2_1_C21":0.05},
        "JPN":{"CPA_2_1_C29":0.20,"CPA_2_1_C":0.87,"CPA_2_1_C26":0.16,
               "CPA_2_1_C28":0.14,"CPA_2_1_C27":0.08,"CPA_2_1_MHRD":0.35,
               "CPA_2_1_HRD":0.15,"CPA_2_1_C303":0.04},
        "USA":{"CPA_2_1_C303":0.10,"CPA_2_1_C26":0.12,"CPA_2_1_C":0.77,
               "CPA_2_1_C21":0.09,"CPA_2_1_C29":0.08,"CPA_2_1_HRD":0.20,
               "CPA_2_1_A":0.11,"CPA_2_1_EPA":0.05},
        "SAU":{"CPA_2_1_EPA":0.75,"CPA_2_1_B06":0.72,"CPA_2_1_C20":0.08},
        "RUS":{"CPA_2_1_EPA":0.58,"CPA_2_1_B06":0.50,"CPA_2_1_C20":0.06},
        "AUS":{"CPA_2_1_A":0.22,"CPA_2_1_B":0.28,"CPA_2_1_B06":0.12,"CPA_2_1_EPA":0.20},
    }
    default_sectors = {
        "CPA_2_1_C":0.70,"CPA_2_1_C26":0.10,"CPA_2_1_C29":0.08,
        "CPA_2_1_C28":0.07,"CPA_2_1_A":0.08,"CPA_2_1_EPA":0.06,
        "CPA_2_1_MHRD":0.20,"CPA_2_1_HRD":0.08,"CPA_2_1_MLRD":0.15,
        "CPA_2_1_C10T12":0.05,"CPA_2_1_C20":0.06,"CPA_2_1_C21":0.04,
    }

    rows = []
    # 動態生成 year_growth，避免 YEARS 超出硬編碼範圍
    base_year_idx = {y: i for i, y in enumerate(sorted(YEARS))}
    year_growth = {y: round(1.0 + 0.05 * i, 4) for y, i in base_year_idx.items()}

    for year in YEARS:
        gf = year_growth[year]
        for exporter in MAIN_COUNTRIES:
            base = base_exp.get(exporter, 30000) * gf
            noise = random.uniform(0.95,1.05)
            # 總計 to World
            rows.append({"年份":year,"出口國家":exporter,"進口國家":"W","產業編號":"_T","數值":base*noise})
            # 對口國分解
            pw = partner_weights.get(exporter, default_partners)
            for partner, w in pw.items():
                if partner in MAIN_COUNTRIES:
                    rows.append({"年份":year,"出口國家":exporter,"進口國家":partner,
                                 "產業編號":"_T","數值":base*w*random.uniform(0.92,1.08)})
            # 產業分解 to World
            sw = sector_weights.get(exporter, default_sectors)
            for prod, w in sw.items():
                rows.append({"年份":year,"出口國家":exporter,"進口國家":"W",
                             "產業編號":prod,"數值":base*w*random.uniform(0.93,1.07)})
                # 對口國 × 產業
                for partner, pw2 in list(pw.items())[:5]:
                    if partner in MAIN_COUNTRIES:
                        rows.append({"年份":year,"出口國家":exporter,"進口國家":partner,
                                     "產業編號":prod,"數值":base*w*pw2*random.uniform(0.88,1.12)})

        # 進口資料（對稱）— 覆蓋 base_imp 全部國家，地圖才有進口色階
        all_importers = set(MAIN_COUNTRIES) | set(base_imp.keys())
        for importer in all_importers:
            base_i = base_imp.get(importer, 28000) * gf
            noise = random.uniform(0.95,1.05)
            rows.append({"年份":year,"出口國家":"W","進口國家":importer,"產業編號":"_T","數值":base_i*noise})
            pw = partner_weights.get(importer, default_partners)
            for partner, w in pw.items():
                if partner in MAIN_COUNTRIES:
                    rows.append({"年份":year,"出口國家":partner,"進口國家":importer,
                                 "產業編號":"_T","數值":base_i*w*random.uniform(0.92,1.08)})
            sw = sector_weights.get(importer, default_sectors)
            for prod, w in sw.items():
                rows.append({"年份":year,"出口國家":"W","進口國家":importer,
                             "產業編號":prod,"數值":base_i*w*random.uniform(0.93,1.07)})

    df = pd.DataFrame(rows)
    df["數值"] = pd.to_numeric(df["數值"],errors="coerce").fillna(0)
    df = df[df["數值"] > 0]
    print(f"  [Demo] 生成 {len(df):,} 筆參考記錄")
    return df


# ─────────────────────────────────────────────────────────
# OECD API 抓取
# ─────────────────────────────────────────────────────────

def _cache_key(url):
    return hashlib.md5(url.encode()).hexdigest()

def fetch_oecd(ref_area, counterpart, year, retries=3):
    global YEARS
    url = (
        "https://sdmx.oecd.org/sti-public/rest/data/"
        "OECD.STI.PIE,DSD_BTIGE@DF_BTIGE,1.0/"
        f"A.{ref_area}.X.TOTAL..{counterpart}."
        f"?startPeriod={year}&endPeriod={year}"
        "&dimensionAtObservation=AllDimensions"
    )
    cache_path = CACHE_DIR / f"{_cache_key(url)}.pkl"
    if cache_path.exists():
        print(f"  [快取] {ref_area or '*'}→{counterpart or '*'} {year}")
        return pickle.loads(cache_path.read_bytes())

    print(f"  [API ] {ref_area or '*'}→{counterpart or '*'} {year}")
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=120,
                             headers={"Accept":"application/xml",
                                      "User-Agent":"OECD-Trade-GIS/1.0"})
            r.raise_for_status()
            break
        except Exception as e:
            if attempt < retries-1:
                print(f"    重試 {attempt+1}/{retries}…")
                time.sleep(4)
            else:
                print(f"    ❌ 失敗：{e}")
                try:
                    YEARS.remove(str(int(year)))
                except:
                    pass
                return pd.DataFrame()

    soup = BeautifulSoup(r.text, "lxml-xml")
    rows = []
    for rec in soup.find_all(["Series","Obs"]):
        row = {"年份":None,"出口國家":None,"進口國家":None,"產業編號":None,"數值":None}
        for v in rec.find_all("Value"):
            tid,tval = v.get("id"),v.get("value")
            if tid=="TIME_PERIOD":         row["年份"]=tval
            elif tid=="REF_AREA":          row["出口國家"]=tval
            elif tid=="COUNTERPART_AREA":  row["進口國家"]=tval
            elif tid=="PRODUCT":           row["產業編號"]=tval
        obs = rec.find("ObsValue")
        if obs: row["數值"]=obs.get("value")
        if any(row.values()): rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        df["數值"] = pd.to_numeric(df["數值"],errors="coerce").fillna(0)
    cache_path.write_bytes(pickle.dumps(df))
    time.sleep(1.5)
    return df

def test_oecd_connectivity():
    """測試 OECD API 是否可連線"""
    try:
        r = requests.get(
            "https://sdmx.oecd.org/sti-public/rest/data/"
            "OECD.STI.PIE,DSD_BTIGE@DF_BTIGE,1.0/"
            "A.TWN.X.TOTAL..W.?startPeriod=2020&endPeriod=2020"
            "&dimensionAtObservation=AllDimensions",
            timeout=15,
            headers={"Accept":"application/xml","User-Agent":"OECD-Trade-GIS/1.0"}
        )
        return r.status_code == 200
    except:
        return False

def fetch_all_real():
    all_frames = []
    country_str = "+".join(MAIN_COUNTRIES)
    for year in YEARS:
        print(f"\n▶ 年份 {year}")
        df_exp = fetch_oecd(country_str, "", year)
        if not df_exp.empty:
            all_frames.append(df_exp)
        df_imp = fetch_oecd("", country_str, year)
        if not df_imp.empty:
            all_frames.append(df_imp)
    if not all_frames:
        return pd.DataFrame()
    df = pd.concat(all_frames,ignore_index=True)
    df["數值"] = pd.to_numeric(df["數值"],errors="coerce").fillna(0)
    return df[df["數值"]>0]


# ─────────────────────────────────────────────────────────
# 資料整理
# ─────────────────────────────────────────────────────────

def compute_summaries(df):
    out = {}
    df_total = df[df["產業編號"]=="_T"].copy()   # 修正：原本錯寫為 "._T"
    df_T = df[df["產業編號"]=="_T"].copy()

    # 5.1 出口 by country/year
    exp = df_T[df_T["進口國家"]=="W"].groupby(["出口國家","年份"])["數值"].sum().reset_index()
    exp.columns = ["country","year","數值"]
    out["export_by_country_year"] = exp.to_dict("records")

    # 5.2 進口 by country/year（涵蓋資料中所有進口國，地圖色階才完整）
    imp = df_T[df_T["出口國家"]=="W"].groupby(["進口國家","年份"])["數值"].sum().reset_index()
    imp.columns = ["country","year","數值"]
    out["import_by_country_year"] = imp.to_dict("records")

    latest = max(YEARS)

    # 5.3 全球產業出口排名
    sec = df[
        (df["年份"]==latest) &
        #(df["進口國家"]=="W") &
        #(df["進口國家"]=="W_X") &
        (df["產業編號"].isin(KEY_PRODUCTS)) &
        (df["產業編號"]!="_T")
    ].groupby("產業編號")["數值"].sum().reset_index().sort_values("數值",ascending=False).head(20)
    sec["產業名稱"] = sec["產業編號"].map(PRODUCT_MAP).fillna(sec["產業編號"])
    out["global_sector_export_rank"] = sec.to_dict("records")

    # 5.4 出口對口國
    # 5.4 出口對口國（多年度，先 groupby 去重，避免同一國家在排行中重複）
    ep_all = {}
    for y in YEARS:
        d_bil_y = df[
            (df["年份"]==y) &
            (df["產業編號"]=="_T") &
            (~df["進口國家"].isin(["W","W_X"]))
        ].groupby(["出口國家","進口國家"])["數值"].sum().reset_index()
        ep_y = {}
        for c in MAIN_COUNTRIES:
            sub = d_bil_y[d_bil_y["出口國家"]==c].nlargest(10,"數值")[["進口國家","數值"]]
            ep_y[c] = sub.to_dict("records")
        ep_all[y] = ep_y
    out["export_partner_rank_by_year"] = ep_all
    out["export_partner_rank"] = ep_all.get(latest, {})

    # 5.5 進口對口國（多年度，先 groupby 去重）
    ip_all = {}
    for y in YEARS:
        d_bil_y = df[
            (df["年份"]==y) &
            (df["產業編號"]=="_T") &
            (~df["進口國家"].isin(["W","W_X"]))
        ].groupby(["出口國家","進口國家"])["數值"].sum().reset_index()
        ip_y = {}
        for c in MAIN_COUNTRIES:
            sub = d_bil_y[d_bil_y["進口國家"]==c].nlargest(10,"數值")[["出口國家","數值"]]
            ip_y[c] = sub.to_dict("records")
        ip_all[y] = ip_y
    out["import_partner_rank_by_year"] = ip_all
    out["import_partner_rank"] = ip_all.get(latest, {})

    #print('df',df)
    # 5.6 各國出口產業（groupby 去重）
    d_se = df[
        (df["年份"]==latest) &
        #(df["進口國家"]=="W") &
        #(df["進口國家"]=="W_X") &
        (df["產業編號"].isin(KEY_PRODUCTS)) &
        (df["產業編號"]!="_T")
    ].groupby(["出口國家","產業編號"])["數值"].sum().reset_index()
    
    #print('MAIN_COUNTRIES',MAIN_COUNTRIES)
    #print('d_se',d_se)
        
    # 1. 先計算所有在 d_se 中存在的出口國家
    all_export_countries = set(MAIN_COUNTRIES) | set(d_se["出口國家"].unique())
    
    cse = {}
    for c in all_export_countries:  # 改為遍歷聯集後的國家列表
        # 2. 篩選資料
        sub = d_se[d_se["出口國家"] == c].nlargest(10, "數值")[["產業編號", "數值"]].copy()
        
        if not sub.empty:
            sub["產業名稱"] = sub["產業編號"].map(PRODUCT_MAP).fillna(sub["產業編號"])
            cse[c] = sub.to_dict("records")
        else:
            # 選擇性：若您希望空資料不存入，這裡可以略過
            cse[c] = [] 
    
    out["country_sector_export"] = cse

    
    # cse = {}
    # for c in MAIN_COUNTRIES:
    #     sub = d_se[d_se["出口國家"]==c].nlargest(10,"數值")[["產業編號","數值"]].copy()
    #     sub["產業名稱"] = sub["產業編號"].map(PRODUCT_MAP).fillna(sub["產業編號"])
    #     cse[c] = sub.to_dict("records")
    # print('cse',cse)
    # out["country_sector_export"] = cse




    

    # 5.7 各國進口產業（groupby 去重，涵蓋所有在資料中出現的進口國）
    #print('df',df)
    d_si = df[
        (df["年份"]==latest) &
        #(df["出口國家"]=="W") &
        #(df["出口國家"]=="W_X") &
        (df["產業編號"].isin(KEY_PRODUCTS)) &
        (df["產業編號"]!="_T")
    ].groupby(["進口國家","產業編號"])["數值"].sum().reset_index()


    
    # 涵蓋 MAIN_COUNTRIES + 資料中出現的所有進口國
    all_import_countries = set(MAIN_COUNTRIES) | set(d_si["進口國家"].unique())
    
    #print('all_import_countries',all_import_countries)
    #print('d_si',d_si)
    csi = {}
    for c in all_import_countries:
        sub = d_si[d_si["進口國家"]==c].nlargest(10,"數值")[["產業編號","數值"]].copy()
        if not sub.empty:
            sub["產業名稱"] = sub["產業編號"].map(PRODUCT_MAP).fillna(sub["產業編號"])
            csi[c] = sub.to_dict("records")
    #print('csi',csi)
    out["country_sector_import"] = csi

    # 5.8 產業出口國排名（多年度）
    ser_all = {}
    for y in YEARS:
        d_sexp_y = df[
            (df["年份"]==y) &
            #(df["進口國家"]=="W") &
            #(df["進口國家"]=="W_X") &
            (df["產業編號"].isin(KEY_PRODUCTS))
        ]
        ser_y = {}
        for prod in KEY_PRODUCTS:
            sub = d_sexp_y[
                (d_sexp_y["產業編號"]==prod) &
                (d_sexp_y["出口國家"].isin(MAIN_COUNTRIES))
            ].groupby("出口國家")["數值"].sum().reset_index().nlargest(15,"數值")[["出口國家","數值"]]
            ser_y[prod] = sub.to_dict("records")
        ser_all[y] = ser_y
    out["sector_exporter_rank_by_year"] = ser_all
    # 保留舊 key（相容）
    out["sector_exporter_rank"] = ser_all.get(latest, {})

    # 5.9 年度變化
    yoy_df = df[
        #(df["進口國家"]=="W") &
        #(df["進口國家"]=="W_X") &
        (df["產業編號"]=="_T")
    ].groupby(["出口國家","年份"])["數值"].sum().reset_index()
    yoy = {}
    for c in MAIN_COUNTRIES:
        sub = yoy_df[yoy_df["出口國家"]==c].sort_values("年份")
        vals = sub.set_index("年份")["數值"].to_dict()
        series = [{"year":y,"value":round(vals.get(y,0),1)} for y in YEARS]
        first = vals.get(YEARS[0],0)
        last  = vals.get(YEARS[-1],0)
        chg = round((last-first)/first*100,1) if first>0 else 0
        yoy[c] = {"series":series,"change_pct":chg}
    out["yoy_export"] = yoy

    # 5.10 雙邊貿易流量（多年度，groupby 去重，排除 W/WX）
    fl_all = {}
    for y in YEARS:
        fl_y = df[
            (df["年份"]==y) &
            (df["產業編號"]=="_T") &
            (~df["出口國家"].isin(["W","W_X"])) &
            (~df["進口國家"].isin(["W","W_X"]))
        ].groupby(["出口國家","進口國家"])["數值"].sum().reset_index()
        fl_all[y] = fl_y.sort_values("數值",ascending=False).head(120).to_dict("records")
    out["bilateral_flows_by_year"] = fl_all
    # 保留舊 key 相容
    out["top_bilateral_flows"] = fl_all.get(latest, [])

    # 5.11 全球出口排名（多年度，供前端依 year 切換）
    gr_all = {}
    for y in YEARS:
        gr = df[
            (df["年份"]==y) &
            #(df["進口國家"]=="W") &
            #(df["進口國家"]=="W_X") &
            (df["產業編號"]=="_T") &
            (df["出口國家"].isin(MAIN_COUNTRIES))
        ].groupby("出口國家")["數值"].sum().reset_index().sort_values("數值",ascending=False)
        gr_all[y] = gr.to_dict("records")
    out["global_export_rank_by_year"] = gr_all
    # 保留舊 key（相容）
    out["global_export_rank"] = gr_all.get(latest, [])

    # 5.12 各國產業對口國
    d_csp = df[
        (df["年份"]==latest) &
        (df["產業編號"].isin(KEY_PRODUCTS)) &
        (df["出口國家"].isin(MAIN_COUNTRIES)) &
        (~df["進口國家"].isin(["W","W_X"]))
    ]
    csp = {}
    for c in MAIN_COUNTRIES:
        csp[c] = {}
        for prod in KEY_PRODUCTS:
            sub = d_csp[
                (d_csp["出口國家"]==c) &
                (d_csp["產業編號"]==prod)
            ].nlargest(5,"數值")[["進口國家","數值"]].to_dict("records")
            if sub: csp[c][prod] = sub
    out["country_sector_partners"] = csp

    out.update({
        "years":YEARS,"latest_year":latest,
        "countries_meta":COUNTRY_META,
        "iso3_to_geojson":ISO3_TO_GEOJSON,
        "product_map":PRODUCT_MAP,
        "key_products":KEY_PRODUCTS,
    })
    return out


# ─────────────────────────────────────────────────────────
# HTML 生成
# ─────────────────────────────────────────────────────────

def generate_html(data, is_demo=False):
    data_json = json.dumps(data, ensure_ascii=False, separators=(",",":"))
    demo_banner = (
        '<div id="demo-banner" style="position:fixed;bottom:0;left:0;right:0;'
        'z-index:2000;background:#1a1000;border-top:1px solid #ff8c00;'
        'padding:6px 16px;font-size:11px;color:#ff8c00;text-align:center;letter-spacing:.5px;">'
        '⚠ Demo 模式 — 使用參考資料（真實量級）。執行 <code>python build_trade_dashboard.py --real</code> 可改用 OECD 真實數據</div>'
    ) if is_demo else ""

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>全球貿易 GIS 儀表板 · OECD BTIGE</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&family=Space+Mono:wght@400;700&family=Bebas+Neue&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#07080e;--bg2:#0d0f1a;--bg3:#131625;--border:#1c2038;
  --accent:#00d4ff;--accent2:#ff6b35;--accent3:#7cff6b;
  --text:#dde6f4;--text2:#7a8699;--text3:#3a4458;
  --gold:#ffd166;--red:#ff3355;--green:#00e676;
  --font-ui:'Noto Sans TC',sans-serif;
  --font-mono:'Space Mono',monospace;
  --font-disp:'Bebas Neue',sans-serif;
  --panel-w:440px;--topbar-h:54px;
}}
body{{background:var(--bg);color:var(--text);font-family:var(--font-ui);overflow:hidden;height:100vh;display:flex;flex-direction:column}}

/* ── topbar ── */
#topbar{{height:var(--topbar-h);background:linear-gradient(90deg,var(--bg2) 0%,#0b0e1c 100%);border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 14px;gap:10px;flex-shrink:0;position:relative;z-index:1001;}}
.logo{{font-family:var(--font-disp);font-size:22px;letter-spacing:3px;color:var(--accent);white-space:nowrap;}}
.logo-sub{{font-size:10px;color:var(--text2);letter-spacing:1.5px;text-transform:uppercase;margin-top:1px;}}
.ctrl-grp{{display:flex;align-items:center;gap:6px;margin-left:auto;flex-wrap:wrap;}}
.ctrl-lbl{{font-size:10px;color:var(--text2);white-space:nowrap;letter-spacing:.5px;}}
select{{background:var(--bg3);border:1px solid var(--border);color:var(--text);font-family:var(--font-ui);font-size:12px;padding:4px 8px;border-radius:5px;cursor:pointer;outline:none;}}
select:hover{{border-color:var(--accent)}}
button.pill{{background:var(--bg3);border:1px solid var(--border);color:var(--text2);font-family:var(--font-ui);font-size:11px;padding:5px 11px;border-radius:20px;cursor:pointer;transition:.15s;letter-spacing:.3px;}}
button.pill:hover{{border-color:var(--accent);color:var(--accent);}}
button.pill.active{{background:var(--accent);color:#000;border-color:var(--accent);font-weight:700;}}
button.pill.active-imp{{background:var(--accent2);color:#fff;border-color:var(--accent2);font-weight:700;}}
.vdiv{{width:1px;height:26px;background:var(--border);margin:0 3px;}}

/* ── layout ── */
#main{{display:flex;flex:1;overflow:hidden;position:relative;}}
#map{{flex:1;}}
#sidebar{{width:var(--panel-w);background:var(--bg2);border-left:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden;flex-shrink:0;transition:transform .28s cubic-bezier(.4,0,.2,1);position:relative;z-index:100;}}
#sidebar.hidden{{transform:translateX(100%);}}
#toggle-sb{{position:absolute;top:50%;right:0;transform:translateY(-50%);z-index:101;background:var(--bg3);border:1px solid var(--border);border-right:none;color:var(--text2);padding:10px 5px;cursor:pointer;border-radius:7px 0 0 7px;font-size:14px;transition:.2s;}}
#toggle-sb:hover{{color:var(--accent)}}

/* ── sidebar tabs ── */
#stabs{{display:flex;border-bottom:1px solid var(--border);flex-shrink:0;background:var(--bg);}}
.stab{{flex:1;padding:10px 4px;font-size:11px;letter-spacing:.5px;text-align:center;cursor:pointer;color:var(--text2);border-bottom:2px solid transparent;transition:.15s;}}
.stab:hover{{color:var(--text)}}
.stab.active{{color:var(--accent);border-bottom-color:var(--accent);background:var(--bg2);}}
#sbody{{flex:1;overflow-y:auto;padding:14px 12px;}}
#sbody::-webkit-scrollbar{{width:3px}}
#sbody::-webkit-scrollbar-thumb{{background:var(--border);border-radius:2px}}

/* ── country header ── */
.ch{{padding:12px 0 10px;border-bottom:1px solid var(--border);margin-bottom:10px;}}
.ch-en{{font-size:10px;color:var(--text2);letter-spacing:1.5px;text-transform:uppercase;}}
.ch-zh{{font-size:28px;font-weight:700;line-height:1.1;}}
.ch-region{{display:inline-block;margin-top:5px;padding:2px 9px;font-size:10px;border-radius:20px;background:var(--bg3);border:1px solid var(--border);color:var(--text2);}}
.kpi-grid{{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:10px 0;}}
.kpi{{background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:9px 12px;}}
.kpi-lbl{{font-size:10px;color:var(--text2);margin-bottom:3px;letter-spacing:.3px;}}
.kpi-v{{font-size:20px;font-weight:700;font-family:var(--font-mono);color:var(--accent);line-height:1;}}
.kpi-v.imp{{color:var(--accent2)}}
.kpi-v.pos{{color:var(--green)}}
.kpi-v.neg{{color:var(--red)}}
.kpi-sub{{font-size:10px;color:var(--text2);margin-top:2px;}}

/* ── section title ── */
.st{{font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:var(--text2);margin:14px 0 7px;display:flex;align-items:center;gap:6px;}}
.st::after{{content:'';flex:1;height:1px;background:var(--border);}}

/* ── bar list ── */
.bl{{display:flex;flex-direction:column;gap:3px;}}
.bi{{display:flex;align-items:center;gap:7px;padding:5px 8px;border-radius:6px;background:var(--bg3);font-size:12px;cursor:pointer;transition:.12s;border-left:2px solid transparent;}}
.bi:hover{{background:#171d32;border-left-color:var(--accent);}}
.bi-rk{{width:18px;text-align:center;font-family:var(--font-mono);font-size:10px;color:var(--text3);flex-shrink:0;}}
.bi-nm{{flex:1;color:var(--text);min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.bi-nm small{{color:var(--text3);font-size:10px;}}
.bi-vl{{font-family:var(--font-mono);font-size:11px;color:var(--text2);white-space:nowrap;flex-shrink:0;}}
.bi-tr{{flex:none;width:50px;height:3px;background:var(--bg);border-radius:2px;overflow:hidden;}}
.bi-fl{{height:100%;border-radius:2px;transition:width .4s ease;}}
.fl-exp{{background:var(--accent)}}
.fl-imp{{background:var(--accent2)}}
.fl-sec{{background:var(--accent3)}}

/* ── yoy bar ── */
.yoy-wrap{{display:flex;align-items:flex-end;gap:3px;height:36px;margin:5px 0 2px;}}
.yoy-col{{flex:1;border-radius:2px 2px 0 0;min-height:3px;cursor:default;position:relative;transition:opacity .2s;}}
.yoy-col:hover{{opacity:.8;}}
.yoy-col::after{{content:attr(data-tip);position:absolute;bottom:110%;left:50%;transform:translateX(-50%);white-space:nowrap;background:var(--bg);border:1px solid var(--border);padding:2px 7px;border-radius:4px;font-size:10px;color:var(--text);pointer-events:none;z-index:99;display:none;}}
.yoy-col:hover::after{{display:block;}}
.yoy-lbs{{display:flex;justify-content:space-between;font-size:9px;color:var(--text3);font-family:var(--font-mono);margin-bottom:6px;}}

/* ── chip list ── */
.chips{{display:flex;flex-wrap:wrap;gap:3px;margin:5px 0;}}
.chip{{padding:3px 9px;border-radius:20px;font-size:10px;cursor:pointer;background:var(--bg3);border:1px solid var(--border);color:var(--text2);transition:.12s;}}
.chip:hover,.chip.act{{background:var(--accent);color:#000;border-color:var(--accent);font-weight:700;}}

/* ── global stats ── */
.gstat{{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;margin-bottom:10px;}}

/* ── legend ── */
#legend{{position:absolute;bottom:24px;left:14px;z-index:999;background:var(--bg2);border:1px solid var(--border);border-radius:9px;padding:10px 14px;min-width:170px;}}
#legend h4{{font-size:10px;letter-spacing:1px;color:var(--text2);margin-bottom:7px;text-transform:uppercase;}}
.leg-sc{{display:flex;gap:2px;margin-bottom:4px;}}
.leg-sw{{height:7px;border-radius:2px;flex:1;}}
.leg-lb{{display:flex;justify-content:space-between;font-size:9px;color:var(--text2);font-family:var(--font-mono);}}

/* ── flow badge ── */
.fbadge{{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:12px;font-size:10px;background:var(--bg3);border:1px solid var(--border);cursor:pointer;margin:2px;}}
.fbadge:hover{{border-color:var(--accent)}}
.fd{{width:5px;height:5px;border-radius:50%;}}

/* ── loading ── */
#loading{{position:fixed;inset:0;background:var(--bg);z-index:9999;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:14px;}}
#loading h2{{font-family:var(--font-disp);font-size:40px;letter-spacing:5px;color:var(--accent);}}
#loading p{{color:var(--text2);font-size:12px;letter-spacing:1px;}}
.spin{{width:36px;height:36px;border:3px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:sp .75s linear infinite;}}
@keyframes sp{{to{{transform:rotate(360deg)}}}}

/* ── tag ── */
.tag{{display:inline-block;padding:1px 6px;font-size:9px;border-radius:4px;background:rgba(0,212,255,.12);color:var(--accent);border:1px solid rgba(0,212,255,.2);margin-left:3px;vertical-align:middle;}}
.tag.i{{background:rgba(255,107,53,.12);color:var(--accent2);border-color:rgba(255,107,53,.2);}}
.empty{{text-align:center;padding:36px 0;color:var(--text3);font-size:13px;}}
.empty span{{display:block;font-size:32px;margin-bottom:8px;}}

/* ── leaflet overrides ── */
.leaflet-container{{background:#06070c!important;}}
.leaflet-control-zoom a{{background:var(--bg2)!important;color:var(--text)!important;border-color:var(--border)!important;}}
.leaflet-tooltip{{background:var(--bg2);border:1px solid var(--border);color:var(--text);font-family:var(--font-ui);font-size:13px;padding:7px 12px;border-radius:8px;box-shadow:0 4px 24px rgba(0,0,0,.7);}}
.leaflet-tooltip::before{{display:none;}}
.leaflet-popup-content-wrapper{{background:var(--bg2);border:1px solid var(--border);color:var(--text);border-radius:10px;box-shadow:0 8px 36px rgba(0,0,0,.85);}}
.leaflet-popup-tip{{background:var(--bg2);}}
</style>
</head>
<body>

<div id="loading">
  <div class="spin"></div>
  <h2>TRADE GIS</h2>
  <p id="lmsg">載入中…</p>
</div>

<div id="topbar">
  <div>
    <div class="logo">▸ GLOBAL TRADE GIS</div>
    <div class="logo-sub">OECD BTIGE · 國際貿易地理資訊系統</div>
  </div>
  <div class="vdiv"></div>
  <div class="ctrl-grp">
    <span class="ctrl-lbl">年份</span>
    <select id="sel-year"></select>
    <div class="vdiv"></div>
    <span class="ctrl-lbl">模式</span>
    <button class="pill active" id="btn-exp" onclick="setMode('export')">📤 出口</button>
    <button class="pill" id="btn-imp" onclick="setMode('import')">📥 進口</button>
    <div class="vdiv"></div>
    <span class="ctrl-lbl">色階</span>
    <select id="sel-sc">
      <option value="log">對數</option>
      <option value="linear">線性</option>
    </select>
    <div class="vdiv"></div>
    <button class="pill" id="btn-fl" onclick="toggleFlows()">📡 流量線</button>
    <button class="pill" onclick="resetView()">⌂ 重置</button>
  </div>
</div>

<div id="main">
  <div id="map"></div>
  <div id="sidebar">
    <div id="stabs">
      <div class="stab active" onclick="switchTab('country')" id="tab-country">🌍 國家分析</div>
      <div class="stab" onclick="switchTab('global')" id="tab-global">🏆 全球排名</div>
      <div class="stab" onclick="switchTab('sector')" id="tab-sector">🏭 產業分析</div>
    </div>
    <div id="sbody">
      <div class="empty"><span>🗺️</span>點擊地圖上的國家<br>查看詳細貿易分析</div>
    </div>
  </div>
  <button id="toggle-sb" onclick="toggleSidebar()">◀</button>
</div>

<div id="legend">
  <h4 id="leg-title">出口總量 (百萬美元)</h4>
  <div class="leg-sc" id="leg-sc"></div>
  <div class="leg-lb"><span id="leg-min">0</span><span id="leg-max">—</span></div>
</div>

{demo_banner}

<script>
// ════════════════ DATA ════════════════
const D = {data_json};
const YEARS = D.years;
const LATEST = D.latest_year;
const CM = D.countries_meta;
const PM = D.product_map;
const KP = D.key_products;
const I2G = D.iso3_to_geojson;

// Build lookup tables
const expM={{}}, impM={{}};
YEARS.forEach(y=>{{ expM[y]={{}}; impM[y]={{}}; }});
D.export_by_country_year.forEach(r=>{{ if(expM[r.year]) expM[r.year][r.country]=r['數值']; }});
D.import_by_country_year.forEach(r=>{{ if(impM[r.year]) impM[r.year][r.country]=r['數值']; }});

// ════════════════ STATE ════════════════
let mode='export', year=LATEST, country=null, tab='country';
let showFlows=false, sbOpen=true, scale='log';
let geoLayer=null, flowLayer=null;

// ════════════════ MAP ════════════════
const map = L.map('map',{{center:[20,10],zoom:2,zoomControl:true,attributionControl:false,preferCanvas:true}});
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_nolabels/{{z}}/{{x}}/{{y}}{{r}}.png',{{maxZoom:19,subdomains:'abcd'}}).addTo(map);

function getColor(val,minV,maxV,m){{
  if(!val||val<=0) return '#111520';
  const t = scale==='log'
    ? Math.log1p(val)/Math.log1p(maxV)
    : Math.min(val/maxV,1);
  const cl = m==='export'
    ? [[7,8,14],[0,80,120],[0,180,220],[100,230,255],[200,248,255]]
    : [[7,8,14],[120,40,0],[200,80,30],[255,120,60],[255,210,170]];
  const n=cl.length-1, i=Math.min(Math.floor(t*n),n-1), f=t*n-i;
  const [a,b]=[cl[i],cl[i+1]];
  return `rgb(${{Math.round(a[0]+(b[0]-a[0])*f)}},${{Math.round(a[1]+(b[1]-a[1])*f)}},${{Math.round(a[2]+(b[2]-a[2])*f)}})`;
}}

const GURL='https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json';
let worldGeo=null;

function styleF(f,minV,maxV){{
  const name=f.properties.name;
  const iso3=Object.entries(I2G).find(([k,v])=>v===name)?.[0];
  const val=iso3?getVal(iso3):0;
  const sel=iso3&&iso3===country;
  return {{
    fillColor:getColor(val,minV,maxV,mode),
    fillOpacity:0.85,
    color:sel?(mode==='export'?'#00d4ff':'#ff6b35'):'#1c2038',
    weight:sel?2.5:0.4,opacity:1
  }};
}}

function updateMap(){{
  if(!worldGeo) return;
  const [mn,mx]=getMinMax();
  updateLegend(mn,mx);
  geoLayer.setStyle(f=>styleF(f,mn,mx));
  updateFlows();
}}

function initMap(){{
  document.getElementById('lmsg').textContent='載入世界地圖…';
  fetch(GURL).then(r=>r.json()).then(geo=>{{
    worldGeo=geo;
    const [mn,mx]=getMinMax();
    geoLayer=L.geoJSON(geo,{{
      style:f=>styleF(f,mn,mx),
      onEachFeature(f,l){{
        const name=f.properties.name;
        const iso3=Object.entries(I2G).find(([k,v])=>v===name)?.[0];
        l.on({{
          mouseover(e){{
            const val=iso3?getVal(iso3):0;
            const zh=(CM[iso3]||{{}}).zh||name;
            l.setStyle({{weight:2,color:'rgba(255,255,255,0.3)'}});
            l.bindTooltip(`<b>${{zh}}</b><br><span style="color:var(--accent);font-family:Space Mono">${{fmt(val)}} M USD</span>`,{{sticky:true}}).openTooltip(e.latlng);
          }},
          mouseout(){{
            const [mn,mx]=getMinMax();
            geoLayer.resetStyle(l);
            if(iso3===country) l.setStyle({{color:mode==='export'?'#00d4ff':'#ff6b35',weight:2.5}});
            l.closeTooltip();
          }},
          click(){{ if(iso3) selectCountry(iso3); }}
        }});
      }}
    }}).addTo(map);
    updateLegend(mn,mx);
    document.getElementById('loading').style.display='none';
  }}).catch(e=>{{document.getElementById('lmsg').textContent='⚠ 地圖載入失敗：'+e.message;}});
}}

// ════════════════ CONTROLS ════════════════
function populateYears(){{
  const s=document.getElementById('sel-year');
  [...YEARS].reverse().forEach(y=>{{
    const o=document.createElement('option');
    o.value=y;o.textContent=y;if(y===LATEST)o.selected=true;s.appendChild(o);
  }});
  s.addEventListener('change',e=>{{year=e.target.value;updateMap();renderTab();}});
}}

function setMode(m){{
  mode=m;
  document.getElementById('btn-exp').className='pill'+(m==='export'?' active':'');
  document.getElementById('btn-imp').className='pill'+(m==='import'?' active-imp':'');
  document.getElementById('leg-title').textContent=m==='export'?'出口總量 (M USD)':'進口總量 (M USD)';
  updateMap();renderTab();
}}

document.getElementById('sel-sc').addEventListener('change',e=>{{scale=e.target.value;updateMap();}});
function resetView(){{map.setView([20,10],2);}}
function toggleSidebar(){{
  sbOpen=!sbOpen;
  document.getElementById('sidebar').classList.toggle('hidden',!sbOpen);
  document.getElementById('toggle-sb').textContent=sbOpen?'▶':'◀';
}}
function switchTab(t){{
  tab=t;
  ['country','global','sector'].forEach(x=>document.getElementById('tab-'+x).classList.toggle('active',x===t));
  renderTab();
}}

// ════════════════ FLOWS ════════════════
function toggleFlows(){{
  showFlows=!showFlows;
  document.getElementById('btn-fl').classList.toggle('active',showFlows);
  updateMap(); // 重繪地圖色階（雙邊模式 ↔ 全球模式切換）
}}

// 取得當前年份的雙邊流量資料（已排除 W/WX）
function getBilateralFlows(){{
  const byYear=D.bilateral_flows_by_year||{{}};
  return byYear[year]||D.top_bilateral_flows||[];
}}

// 取得以 country 為基準的雙邊流量 lookup → {{ iso3: 數值 }}
function getBilateralLookup(){{
  if(!country||!showFlows) return null;
  const all=getBilateralFlows();
  const lookup={{}};
  if(mode==='export'){{
    // 出口模式：country → 各夥伴國的出口量
    all.filter(f=>f['出口國家']===country).forEach(f=>{{
      const k=f['進口國家'];
      lookup[k]=(lookup[k]||0)+f['數值'];
    }});
  }} else {{
    // 進口模式：各夥伴國 → country 的出口量（country 的進口來源）
    all.filter(f=>f['進口國家']===country).forEach(f=>{{
      const k=f['出口國家'];
      lookup[k]=(lookup[k]||0)+f['數值'];
    }});
  }}
  return lookup;
}}

function getVal(iso3){{
  // 流量線開啟且有選國家 → 用雙邊流量著色地圖
  if(showFlows&&country){{
    const lk=getBilateralLookup();
    return (lk&&lk[iso3])||0;
  }}
  return ((mode==='export'?expM:impM)[year]||{{}})[iso3]||0;
}}

function getMinMax(){{
  if(showFlows&&country){{
    // 以當前國家的雙邊流量範圍為色階基準
    const lk=getBilateralLookup();
    if(lk){{
      const vals=Object.values(lk).filter(v=>v>0);
      if(vals.length) return [0,Math.max(...vals)];
    }}
  }}
  const vals=Object.values((mode==='export'?expM:impM)[year]||{{}}).filter(v=>v>0);
  return [Math.min(...vals)||0,Math.max(...vals)||1];
}}

function updateFlows(){{
  if(flowLayer){{flowLayer.remove();flowLayer=null;}}
  if(!showFlows) return;
  const all=getBilateralFlows();
  // 有選國家 → 只顯示與該國相關的流量線
  const fl=country
    ? all.filter(f=>f['出口國家']===country||f['進口國家']===country).slice(0,30)
    : all.slice(0,50);
  if(!fl.length) return;

  const mx=Math.max(...fl.map(f=>f['數值']),1);
  const lines=fl.map(f=>{{
    const from=CM[f['出口國家']],to=CM[f['進口國家']];
    if(!from||!to) return null;
    const raw=f['數值'];
    // 線條粗細也跟著 scale 設定走
    const t=scale==='log'
      ? Math.log1p(raw)/Math.log1p(mx)
      : Math.min(raw/mx,1);
    // 有選國家時：出口線（country→X）用青色，進口線（X→country）用橙色；無選時跟 mode 走
    let baseColor;
    if(country){{
      //baseColor=f['出口國家']===country?'0,212,255':'255,107,53';
      baseColor=mode==='export'?'0,212,255':'255,107,53';
    }} else {{
      baseColor=mode==='export'?'0,212,255':'255,107,53';
    }}
    return L.polyline([[from.lat,from.lng],[to.lat,to.lng]],{{
      color:`rgba(${{baseColor}},${{0.25+t*0.6}})`,
      weight:0.8+t*4,opacity:1,
    }});
  }}).filter(Boolean);
  flowLayer=L.layerGroup(lines).addTo(map);
}}

// ════════════════ LEGEND ════════════════
function updateLegend(mn,mx){{
  const sc=document.getElementById('leg-sc');sc.innerHTML='';
  for(let i=0;i<8;i++){{
    const t=i/7;
    const v=scale==='log'?Math.expm1(t*Math.log1p(mx)):mn+(mx-mn)*t;
    const d=document.createElement('div');d.className='leg-sw';
    d.style.background=getColor(v+1,mn,mx,mode);sc.appendChild(d);
  }}
  document.getElementById('leg-min').textContent='0';
  document.getElementById('leg-max').textContent=fmt(mx);
  // 標題：雙邊模式 vs 全球模式
  const title=document.getElementById('leg-title');
  if(showFlows&&country){{
    const zh_c=(CM[country]||{{}}).zh||country;
    title.textContent=mode==='export'
      ? `${{zh_c}} 出口至各國 (M USD)`
      : `${{zh_c}} 進口來源 (M USD)`;
  }} else {{
    title.textContent=mode==='export'?'出口總量 (M USD)':'進口總量 (M USD)';
  }}
}}

// ════════════════ FORMAT ════════════════
function fmt(v){{
  if(!v||v===0) return '—';
  if(v>=1e6) return (v/1e6).toFixed(2)+'T';
  if(v>=1e3) return (v/1e3).toFixed(1)+'B';
  return Math.round(v).toLocaleString()+'M';
}}
function fmtPct(p){{return (p>=0?'+':'')+p.toFixed(1)+'%';}}
function zh(iso3){{return (CM[iso3]||{{}}).zh||iso3;}}
function pn(code){{return PM[code]||code;}}

// ════════════════ COUNTRY SELECT ════════════════
function selectCountry(iso3){{
  country=iso3;
  if(!sbOpen) toggleSidebar();
  switchTab('country');
  updateMap();
}}

// ════════════════ RENDER ════════════════
function renderTab(){{
  if(tab==='country') renderCountry();
  else if(tab==='global') renderGlobal();
  else renderSector();
}}

// ── Country ──────────────────────────────
function renderCountry(){{
  const b=document.getElementById('sbody');
  if(!country){{b.innerHTML='<div class="empty"><span>🗺️</span>點擊地圖上的國家<br>查看詳細貿易分析</div>';return;}}
  const m=CM[country]||{{}};
  const ev=(expM[year]||{{}})[country]||0;
  const iv=(impM[year]||{{}})[country]||0;
  const bal=ev-iv;
  const yo=(D.yoy_export||{{}})[country]||{{series:[],change_pct:0}};
  const chg=yo.change_pct;
  const sv=yo.series.map(s=>s.value);
  const smx=Math.max(...sv,1);
  const yBars=yo.series.map(s=>{{
    const h=Math.max(3,Math.round(s.value/smx*32));
    const col=s.year===year?'var(--accent)':'#1e3a4a';
    return `<div class="yoy-col" style="height:${{h}}px;background:${{col}}" data-tip="${{s.year}}: ${{fmt(s.value)}}"></div>`;
  }}).join('');

  const epByYear=D.export_partner_rank_by_year||{{}};
  const ipByYear=D.import_partner_rank_by_year||{{}};
  const ep=((epByYear[year]||D.export_partner_rank||{{}})[country])||[];
  const ip=((ipByYear[year]||D.import_partner_rank||{{}})[country])||[];
  const mep=ep.length?ep[0]['數值']:1, mip=ip.length?ip[0]['數值']:1;


  console.log("Country:", country);
  console.log("SE Raw Data:", D.country_sector_export ? D.country_sector_export[country] : "Key missing");
  console.log("SI Raw Data:", D.country_sector_import ? D.country_sector_import[country] : "Key missing");


  const se=((D.country_sector_export||{{}})[country]||[]).slice(0,8);
  const si=((D.country_sector_import||{{}})[country]||[]).slice(0,6);
  const mse=se.length?se[0]['數值']:1, msi=si.length?si[0]['數值']:1;

  b.innerHTML=`
<div class="ch">
  <div class="ch-en">${{m.en||country}}</div>
  <div class="ch-zh" style="color:${{mode==='export'?'var(--accent)':'var(--accent2)'}}">${{m.zh||country}}</div>
  <span class="ch-region">${{m.region||'—'}}</span>
</div>
<div class="kpi-grid">
  <div class="kpi">
    <div class="kpi-lbl">📤 出口總量 · ${{year}}</div>
    <div class="kpi-v">${{fmt(ev)}}</div><div class="kpi-sub">M USD</div>
  </div>
  <div class="kpi">
    <div class="kpi-lbl">📥 進口總量 · ${{year}}</div>
    <div class="kpi-v imp">${{fmt(iv)}}</div><div class="kpi-sub">M USD</div>
  </div>
  <div class="kpi">
    <div class="kpi-lbl">⚖ 貿易差額</div>
    <div class="kpi-v ${{bal>=0?'pos':'neg'}}">${{fmt(Math.abs(bal))}} ${{bal>=0?'▲':'▼'}}</div>
    <div class="kpi-sub">${{bal>=0?'順差':'逆差'}}</div>
  </div>
  <div class="kpi">
    <div class="kpi-lbl">📈 出口變化 ${{YEARS[0]}}→${{YEARS[YEARS.length-1]}}</div>
    <div class="kpi-v ${{chg>=0?'pos':'neg'}}">${{fmtPct(chg)}}</div>
    <div class="kpi-sub">累計</div>
  </div>
</div>
<div class="st">出口趨勢</div>
<div class="yoy-wrap">${{yBars}}</div>
<div class="yoy-lbs">${{yo.series.map(s=>`<span>${{s.year}}</span>`).join('')}}</div>
<div class="st">出口對口國 TOP 10 <span class="tag">${{year}}</span></div>
<div class="bl">
${{ep.map((p,i)=>`<div class="bi" onclick="selectCountry('${{p['進口國家']}}')">
  <span class="bi-rk">${{i+1}}</span>
  <span class="bi-nm">${{zh(p['進口國家'])}} <small>${{p['進口國家']}}</small></span>
  <span class="bi-vl">${{fmt(p['數值'])}}</span>
  <div class="bi-tr"><div class="bi-fl fl-exp" style="width:${{Math.round(p['數值']/mep*100)}}%"></div></div>
</div>`).join('')}}
</div>
<div class="st">進口對口國 TOP 10 <span class="tag i">${{year}}</span></div>
<div class="bl">
${{ip.map((p,i)=>`<div class="bi" onclick="selectCountry('${{p['出口國家']}}')">
  <span class="bi-rk">${{i+1}}</span>
  <span class="bi-nm">${{zh(p['出口國家'])}} <small>${{p['出口國家']}}</small></span>
  <span class="bi-vl">${{fmt(p['數值'])}}</span>
  <div class="bi-tr"><div class="bi-fl fl-imp" style="width:${{Math.round(p['數值']/mip*100)}}%"></div></div>
</div>`).join('')}}
</div>
<div class="st">出口產業結構 <span class="tag">${{LATEST}}</span></div>
<div class="bl">
${{se.map((p,i)=>(console.log('即時資料：', i, p),`<div class="bi" onclick="showSP('${{p['產業編號']}}')">
  <span class="bi-rk">${{i+1}}</span>
  <span class="bi-nm">${{p['產業名稱']||pn(p['產業編號'])}}</span>
  <span class="bi-vl">${{fmt(p['數值'])}}</span>
  <div class="bi-tr"><div class="bi-fl fl-sec" style="width:${{Math.round(p['數值']/mse*100)}}%"></div></div>
</div>`)).join('')}}
</div>
<div class="st">進口產業結構 <span class="tag i">${{LATEST}}</span></div>
<div class="bl">
${{si.map((p,i)=>`<div class="bi">
  <span class="bi-rk">${{i+1}}</span>
  <span class="bi-nm">${{p['產業名稱']||pn(p['產業編號'])}}</span>
  <span class="bi-vl">${{fmt(p['數值'])}}</span>
  <div class="bi-tr"><div class="bi-fl fl-imp" style="width:${{Math.round(p['數值']/msi*100)}}%"></div></div>
</div>`).join('')}}
</div>
<div id="sp-panel"></div>`;
}}

function showSP(prod){{
  const p=document.getElementById('sp-panel');
  if(!p||!country) return;
  const pts=((D.country_sector_partners||{{}})[country]||{{}})[prod]||[];
  if(!pts.length){{p.innerHTML='';return;}}
  const mx=pts[0]['數值'];
  p.innerHTML=`<div class="st" style="color:var(--accent3)">${{pn(prod)}} ─ 出口目的地</div>
<div class="bl">
${{pts.map((x,i)=>`<div class="bi" onclick="selectCountry('${{x['進口國家']}}')">
  <span class="bi-rk">${{i+1}}</span>
  <span class="bi-nm">${{zh(x['進口國家'])}}</span>
  <span class="bi-vl">${{fmt(x['數值'])}}</span>
  <div class="bi-tr"><div class="bi-fl fl-sec" style="width:${{Math.round(x['數值']/mx*100)}}%"></div></div>
</div>`).join('')}}
</div>`;
}}

// ── Global ────────────────────────────────
function renderGlobal(){{
  const b=document.getElementById('sbody');
  // 使用多年度資料，依目前 year 切換
  const grByYear=D.global_export_rank_by_year||{{}};
  const gr=(grByYear[year]||D.global_export_rank)||[];
  const srByYear=D.sector_exporter_rank_by_year||{{}};
  const srYear=srByYear[year]||{{}};
  const sr=(srYear[activeSector])||[];
  // 全局產業排名：重新計算該年度各產業總量
  const sectorTotals=KP.filter(p=>p!=='_T').map(p=>{{
    const rows=(srYear[p])||[];
    const total=rows.reduce((s,r)=>s+r['數值'],0);
    return {{prod:p,total}};
  }}).sort((a,b)=>b.total-a.total).slice(0,16);
  const me=gr.length?gr[0]['數值']:1;
  const mst=sectorTotals.length?sectorTotals[0].total:1;
  b.innerHTML=`
<div class="st">全球出口量排名 <span class="tag">${{year}}</span></div>
<div class="bl">
${{gr.slice(0,25).map((r,i)=>{{
  const m=CM[r['出口國家']]||{{}};
  return `<div class="bi" onclick="selectCountry('${{r['出口國家']}}');switchTab('country')">
    <span class="bi-rk">${{i+1}}</span>
    <span class="bi-nm">${{m.zh||r['出口國家']}} <small>${{r['出口國家']}}</small></span>
    <span class="bi-vl">${{fmt(r['數值'])}}</span>
    <div class="bi-tr"><div class="bi-fl fl-exp" style="width:${{Math.round(r['數值']/me*100)}}%"></div></div>
  </div>`;
}}).join('')}}
</div>
<div class="st" style="margin-top:18px">全球產業出口排名 <span class="tag">${{year}}</span></div>
<div class="bl">
${{sectorTotals.map((s,i)=>`<div class="bi" onclick="activeSector='${{s.prod}}';switchTab('sector')">
  <span class="bi-rk">${{i+1}}</span>
  <span class="bi-nm">${{pn(s.prod)}}</span>
  <span class="bi-vl">${{fmt(s.total)}}</span>
  <div class="bi-tr"><div class="bi-fl fl-sec" style="width:${{Math.round(s.total/mst*100)}}%"></div></div>
</div>`).join('')}}
</div>`;
}}

// ── Sector ────────────────────────────────
let activeSector=KP[2];

function renderSector(){{
  const b=document.getElementById('sbody');
  const chips=KP.filter(p=>p!=='_T').map(p=>`
<div class="chip ${{p===activeSector?'act':''}}" onclick="activeSector='${{p}}';renderSector()">
  ${{pn(p).replace('CPA_2_1_','').slice(0,10)}}
</div>`).join('');
  // 使用多年度資料
  const srByYear=D.sector_exporter_rank_by_year||{{}};
  const exp=((srByYear[year]||{{}})[activeSector])||[];
  const mx=exp.length?exp[0]['數值']:1;
  b.innerHTML=`
<div class="st">選擇產業</div>
<div class="chips">${{chips}}</div>
<div class="st" style="margin-top:12px">
  [${{pn(activeSector)}}]<br>出口國排名 <span class="tag">${{year}}</span>
</div>
<div class="bl">
${{exp.slice(0,18).map((r,i)=>{{
  const m=CM[r['出口國家']]||{{}};
  return `<div class="bi" onclick="selectCountry('${{r['出口國家']}}');switchTab('country')">
    <span class="bi-rk">${{i+1}}</span>
    <span class="bi-nm">${{m.zh||r['出口國家']}} <small>${{r['出口國家']}}</small></span>
    <span class="bi-vl">${{fmt(r['數值'])}}</span>
    <div class="bi-tr"><div class="bi-fl fl-sec" style="width:${{Math.round(r['數值']/mx*100)}}%"></div></div>
  </div>`;
}}).join('')}}
</div>`;
}}

// ════════════════ INIT ════════════════
populateYears();
initMap();
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────
# 主程式
# ─────────────────────────────────────────────────────────

def main():
    args = set(sys.argv[1:])
    force_demo = "--demo" in args
    force_real = "--real" in args

    print("="*60)
    print("  OECD Global Trade GIS Dashboard Builder v2.0")
    print("="*60)
    print(f"分析年份：{YEARS}  |  國家數：{len(MAIN_COUNTRIES)}")

    is_demo = False

    if force_demo:
        print("\n▶ 模式：Demo（強制）")
        df = build_demo_data()
        is_demo = True
    elif force_real:
        print("\n▶ 模式：OECD API（強制）")
        df = fetch_all_real()
        if df.empty:
            print("❌ API 無資料，改用 Demo 模式")
            df = build_demo_data(); is_demo = True
    else:
        print("\n▶ 偵測 OECD API 連線…")
        if test_oecd_connectivity():
            print("  ✅ 連線正常 → 使用真實資料")
            df = fetch_all_real()
            if df.empty:
                print("  ⚠ 資料為空，切換 Demo 模式")
                df = build_demo_data(); is_demo = True
        else:
            print("  ⚠ 無法連線 OECD → 使用 Demo 模式")
            df = build_demo_data(); is_demo = True

    if df.empty:
        print("❌ 無任何資料，終止。"); return

    print(f"\n✅ 資料：{len(df):,} 筆")
    print("\n【整理分析維度】")
    summaries = compute_summaries(df)
    print(f"✅ 完成 {len(summaries)} 個分析項目")

    print("\n【產生 HTML】")
    html = generate_html(summaries, is_demo)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    sz = OUTPUT_FILE.stat().st_size // 1024
    print(f"✅ 輸出：{OUTPUT_FILE.resolve()}  ({sz} KB)")
    print("\n" + "="*60)
    print("  使用瀏覽器開啟 index.html 即可")
    if is_demo:
        print("  ⚠ 目前為 Demo 模式；加 --real 可抓取真實 OECD 資料")
    print("="*60)

if __name__ == "__main__":
    update_YEARS()
    update_MAIN_COUNTRIES()
    main()
