# 陸上大会速報システム
## システム概要
陸上大会の速報システムを作りました

大会の速報サイトを定期巡回し,更新された結果データを自動で抽出してGitHub Pagesへリアルタイム配信するシステムです.  
Raspberry Pi 5 で十分実行可能な軽量なHEADリクエスト監視と,GitHub Gist / Pages を活用した設計により,対象サーバーや自前インフラに負荷をかけない運用を実現しています.  

詳細は(((後で記事のリンク貼る)))で公開しています

## 使い方
### 環境構築
システムはLinux(Raspberry Pi OS / WSL等)での運用を想定しています.  
またPythonのシステム保護仕様対応のため`venv`(仮想環境)を利用して構築しています.

### 作業ディレクトリの作成(/.../は好きに書き換えて下さい)
```bash
mkdir -p /.../Sokuhou  
cd /.../Sokuhou
```
### venv インストール（必要な場合）
```bash
sudo apt update  
sudo apt install -y python3-venv python3-pip
```
### 仮想環境有効化・パッケージインストール
```bash
python3 -m venv venv  
source venv/bin/activate
touch requirements.txt //systemディレクトリにあるrequirements.txtの内容をそのまま書き込んで下さい  
pip install -r requirements.txt
```
### ファイル作成
```bash
touch checker.py makelist.py
python3 makelist.py
```
中身を書き込んだ後,makelist.pyを実行すると`target2026.txt`が作成されます  
(※`target2026.txt.example`を参考に手動で作成しても構いません またURLの先頭に# をつけると対象から外すことが出来ます(詳細は`checker.py`に書いてあります))  
これで自動実行する準備は整いました

## 自動実行する方法
電源投入時に自動起動しクラッシュ時にも自動復旧するよう`systemd`サービスとして登録します.
```bash
/etc/systemd/system/track-checker.service
```
のような場所にサービス定義ファイルを作り、track-checker.service の中身を書き込み

sudo systemctl daemon-reload  
sudo systemctl enable track-checker.service

で読み込み・自動実行有効化.電源を入れると自動で起動します.  
※停止・再開は

sudo systemctl stop track-checker.service  
sudo systemctl restart track-checker.service

リアルタイムのログ監視をしたい場合
sudo journalctl -u track-checker.service -f
