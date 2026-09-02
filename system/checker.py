import hashlib
import os
import time
from datetime import datetime, timezone, timedelta
import requests
import json
from bs4 import BeautifulSoup




# -------------------------------------------------------------------
# 設定エリア
# -------------------------------------------------------------------

# 確認対象ページ一覧
URL_FILE = "target2026.txt"

# 巡回インターバル（秒）
CHECK_INTERVAL = 10

# GitHub Gist 設定
GIST_ID = "YOUR_GIST_ID"
GIST_TOKEN = "YOUR_GIST_TOKEN"
# 確認する学校の略称（陸連ページの用いる略称）
TARGET_KEYWORD = "YOUR_TARGET_SCHOOL_NAME"

# 日本時間（JST = UTC+9）の定義
JST = timezone(timedelta(hours=9))

# Dos攻撃判定回避用のHEADER設定
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    )
}

# 過去データを記録する辞書
# 記録形式　{ url: {"head_lm": ..., "head_cl": ..., "get_hash": ...} }
history_data = {}

# -------------------------------------------------------------------


# URL_FILESを取得、#から始まる行を削除
def load_urls():
    if os.path.exists(URL_FILE):
        urls = []
        with open(URL_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
        if urls:
            return urls
    return []


# Gist APIにPATCHリクエストを送り、results.json を更新する
def gist_send(payload_data):
    gist_url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {
        "Authorization": f"Bearer {GIST_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    body = {
        "files": {
            "results.json": {
                "content": json.dumps(payload_data, ensure_ascii=False, indent=2)
            }
        }
    }
   
    try:
        res = requests.patch(gist_url, headers=headers, json=body, timeout=10)
        if res.status_code == 200:
            print(" ✅ Gist へのデータ送信に成功しました！")
        else:
            print(f" ❌ Gist 送信エラー: {res.status_code} - {res.text}")
    except Exception as e:
        print(f" ❌ Gist 通信失敗: {e}")

# HTML本文から対象の学校名が含まれるブロックを抽出・構造化する補助関数
def parse_race_html(html_text, target_keyword=TARGET_KEYWORD):
    soup = BeautifulSoup(html_text, "html.parser")
    race_title = soup.title.text.strip() if soup.title else "タイトル不明"

    # リレー種目の判定（リレーとその他種目で、ページの構成が異なるため区別しておく必要がある）
    is_relay = any(
        k in race_title for k in ["４×", "4×", "４x", "4x", "リレー"]
    )
    results = []
    # 各選手ごとのデータの境は、<font>によって判定
    for font in soup.find_all("font"):
        text = font.get_text()
        if target_keyword not in text:
            continue

        # <br> を改行に置き換えて分割
        for br in font.find_all("br"):
            br.replace_with("\n")


        lines = [
            line.strip()
            for line in font.get_text().split("\n")
            if line.strip()
        ]
        if not lines:
            continue


        if is_relay:
            # 【リレーの抽出】
            results.append({
                "type": "relay",
                "rank_and_record": lines[0] if len(lines) > 0 else "",
                "school": lines[1] if len(lines) > 1 else "",
                "runners": lines[2:] if len(lines) > 2 else [],
            })
        else:
            # 【個人（トラック・走幅跳）の抽出】
            # 注意　大会記録に、例外的な表記（例：大会記録）が記述されると正常に動作しないことを確認済み
            results.append({
                "type": "individual",
                "rank_and_num": lines[0] if len(lines) > 0 else "",
                # "record": " ".join(middle_info) if middl else "",
                "record": lines[1] if len(lines) >= 2 else "",
                "name": lines[2] if len(lines) >= 3 else "",
                "school": lines[3] if len(lines) >= 4 else "",
            })


    return race_title, results

# 更新の確認されたページからGETで最新HTMLを取得し、抽出結果を current_json_data (辞書) に書き込む
def gist_update(url, current_json_data):
    # キャッシュ対策用にURLに時間を追加
    cache_busting_url = f"{url}?_t={int(time.time())}"


    try:
        print(f" 📥 GET実行中... [{url}]")
        res = requests.get(cache_busting_url, headers=HEADERS, timeout=15)
        res.encoding = res.apparent_encoding

        # HTMLを解析して特定の学校の選手データを取得
        race_title, extracted_results = parse_race_html(res.text)

        # JSON保存用データ構造の組み立て
        current_json_data[url] = {
            "race_title": race_title,
            "url": url,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data_count": len(extracted_results),
            "results": extracted_results,
        }

        print(f" ✨ 解析完了 [{race_title}]: {len(extracted_results)}件のデータを格納しました")


    except Exception as e:
        print(f" ❌ GET/解析エラー [{url}]: {e}")

# URLの中身を巡回　更新があればgist_updateを動かす
def run_parallel_verification():
    urls = load_urls()
    if not urls:
        print("⚠️ 監視対象のURLがありません。target.txt を確認してください。")
        return

    json_payload ={}

    while True:
        now_str = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{now_str}] 🔄 巡回チェックを実行中... (対象: {len(urls)}件)", flush=True)


        updated_all = False
        for url in urls:
           
            cache_busting_url = f"{url}?_t={int(time.time())}"
            lm = "N/A"
            cl = "N/A"
            # get_hashはgetリクエスト用の変数
            get_hash = ""


            # ---------------------------------------------------------------
            # 1. HEAD リクエストの実行
            # ---------------------------------------------------------------
            updated = False
           
            try:
                res_head = requests.head(cache_busting_url, headers=HEADERS, timeout=5)
                lm = res_head.headers.get("Last-Modified", "N/A")
                cl = res_head.headers.get("Content-Length", "N/A")
               
            except Exception as e:
                print(f" ⚠️ HEAD通信エラー [{url}]: {e}")


            # ---------------------------------------------------------------
            # 2. GET リクエストの実行 (本文ハッシュ計算)
            # ---------------------------------------------------------------

            # Dos攻撃対策のため、基本的にgetは行わない。万が一headが機能していない場合、
            # この部分を有効化する
            # try:
            #     res_get = requests.get(cache_busting_url, headers=HEADERS, timeout=5)
            #     res_get.encoding = res_get.apparent_encoding
            #     # 本文の SHA-256 ハッシュ値を計算
            #     get_hash = hashlib.sha256(res_get.text.encode("utf-8")).hexdigest()[:12]  
            #     # 先頭12文字のみ表示
            # except Exception as e:
            #     get_hash = "ERROR"

            # ---------------------------------------------------------------
            # 3. 前回データとの比較・判定
            # ---------------------------------------------------------------
            if url not in history_data:
                # 初回記録
                history_data[url] = {
                    "lm": lm,
                    "cl": cl,
                    "hash": get_hash,
                }
                             
                updated = True


            else:
                prev = history_data[url]


                # 変化チェック
                if prev["lm"] != lm or prev["cl"] != cl or prev["hash"] != get_hash:
                    updated = True


                # 結果の出力
            if updated:


                # 履歴を最新に更新
                history_data[url] = {
                    "lm": lm,
                    "cl": cl,
                    "hash": get_hash
                }
                gist_update(url,json_payload)
                updated_all = True


            # リクエスト間の微小待機（マナー保護）
            time.sleep(0.3)
        if updated_all:
            gist_send(json_payload)
        print()

        time.sleep(CHECK_INTERVAL)


# プログラム本体部分
if __name__ == "__main__":
    try:
        run_parallel_verification()
    except KeyboardInterrupt:
        print("\nプログラムを停止しました。")
