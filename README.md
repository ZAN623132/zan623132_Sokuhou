## システム概要
陸上大会の速報システムを作りました
詳細は(((後で記事のリンク貼る)))で公開しています

# 使い方
## 環境構築
仮想環境を利用します(以下linuxを想定)
### フォルダ作成(/.../は好きに書き換えて下さい)
mkdir -p /.../Sokuhou
cd /.../Sokuhou

### venv インストール（なければ）
sudo apt update
sudo apt install -y python3-venv python3-pip

### 仮想環境有効化・パッケージインストール
python3 -m venv venv
source venv/bin/activate
pip install requests beautifulsoup4

### ファイル作成
touch checker.py makelist.py

makelist.pyを実行するとtarget2026.txtが作成されます。
これで自動実行する準備は整いました

## 自動実行する方法
/etc/systemd/system/track-checker.service

のような場所にサービス定義ファイルを作り、track-checker.service の中身を書き込み

sudo systemctl daemon-reload
sudo systemctl enable track-checker.service

で読み込み・自動実行有効化。電源を入れると自動で起動します。
※停止・再開は

sudo systemctl stop track-checker.service
sudo systemctl restart track-checker.service

sudo journalctl -u track-checker.service -f

でリアルタイムのログ監視が可能
