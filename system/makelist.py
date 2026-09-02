import time
import requests
from bs4 import BeautifulSoup

# -------------------------------------------------------------------
# 設定エリア
# -------------------------------------------------------------------
# 陸連の速報ページは、大会ごとに末尾3桁の違いのみでレースごとのページを作っている　ここを総当たりして探る
BASE_URL = "https://example/rel{:03d}.html"
START_NUM = 1
END_NUM = 500

# 対象学校の略称
TARGET_KEYWORD = "YOUR_TARGET_SCHOOL_NAME"

OUTPUT_FILE = "target2026.txt"

# Dos攻撃判定回避用
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    )
}
# -------------------------------------------------------------------

# 対象学校の選手が含まれるURL全てのリストを作る
def make_target_list():
    matched_items = []  # (url, title) のペアを格納する

    for i in range(START_NUM, END_NUM + 1):
        url = BASE_URL.format(i)

        try:
            res = requests.get(url, headers=HEADERS, timeout=3)

            if res.status_code != 200:
                continue

            res.encoding = res.apparent_encoding

            if TARGET_KEYWORD in res.text:
                soup = BeautifulSoup(res.text, "html.parser")
                # title がない場合の安全策（デフォルト値の設定）
                race_title = (
                    soup.title.text.strip() if soup.title else "タイトル不明"
                )

                matched_items.append((url, race_title))

        except Exception as e:
            print(f"⚠️ [{i:03d}] エラー: {e}")

        time.sleep(0.2)

    # 結果を target2026.txt に保存
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(
            f"# '{TARGET_KEYWORD}' 出場種目リスト"
            f" (全{len(matched_items)}件)\n\n"
        )

        for url, title in matched_items:
            # 先にレース名をコメントとして書き出し、次の行にURLを書く（視認性UP）
            f.write(f"# {title}\n")
            f.write(f"{url}\n\n")

    print(
        f"\n🎉 完了！ {len(matched_items)} 件の対象URLを"
        f" '{OUTPUT_FILE}' に保存しました。"
    )

# プログラム本体
if __name__ == "__main__":
    make_target_list()
