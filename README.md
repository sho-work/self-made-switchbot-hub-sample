# self-made-switchbot-hub-sample
自作BLE通信ハブのサンプル

## 概要
Webアプリケーションを使用した顔認証システムです。顔認証が成功するとSwitchBotを自動的に動作させます。

## システム構成
- **バックエンド**: FastAPI (Python)
- **フロントエンド**: Vite + React
- **顔認証**: face-recognition ライブラリ
- **BLE通信**: bleak + switchbot-api

## セットアップ

### 1. 依存関係のインストール
```bash
# Python依存関係
pip install -r requirements.txt

# Node.js依存関係
cd web
npm install
cd ..
```

### 2. 顔画像の登録
`trainings/` ディレクトリに認証したい人の顔画像を配置してください。
- ファイル名が認証時の名前になります（例: `john.jpg` → "john"）
- JPG, JPEG, PNG形式をサポート
- 1人につき1枚の画像を推奨

### 3. アプリケーションの起動

#### 方法1: 一括起動スクリプト
```bash
./start.sh
```

#### 方法2: 個別起動
```bash
# ターミナル1: FastAPIサーバー
cd api
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# ターミナル2: Viteサーバー
cd web
npm run dev
```

## 使い方

1. ブラウザで http://localhost:3000 にアクセス
2. 「認証を開始」ボタンをクリックしてカメラを起動
3. カメラに顔を映すと自動的に認証処理が実行されます
4. 認証成功時、自動的にSwitchBotが動作します

## API エンドポイント

- `GET /api/status` - サーバーステータスの確認
- `POST /api/face_recognition` - 顔認証の実行
- `POST /api/switch_bot/press` - SwitchBotの手動操作
- `POST /api/upload_known_face` - 新しい顔画像のアップロード

## トラブルシューティング

### ECONNREFUSED エラー / APIに接続できない
Viteサーバーから「http proxy error: /api/status」などのエラーが表示される場合：

1. FastAPIサーバーが起動しているか確認:
```bash
curl http://localhost:8000/
```

2. FastAPIサーバーを単独で起動してエラーを確認:
```bash
python3 start_api.py
# または
cd api && python3 -m uvicorn main:app --reload
```

3. 依存関係が正しくインストールされているか確認:
```bash
pip3 install -r requirements.txt
```

4. ポート8000が他のプロセスで使用されていないか確認:
```bash
lsof -i :8000
```

### カメラが起動しない
- ブラウザのカメラ権限を確認してください
- HTTPSまたはlocalhostでのみカメラAPIが動作します
- 他のアプリケーションがカメラを使用していないか確認

### SwitchBotが動作しない
- SwitchBotの電源とBluetooth接続を確認
- スマホアプリを完全終了してから再試行
- macOSの場合、システム環境設定でBluetoothアクセスを許可

### 顔認証が失敗する
- trainingsフォルダに顔画像が正しく配置されているか確認
- 画像に顔が1つだけ含まれているか確認
- 画像ファイル名に日本語や特殊文字が含まれていないか確認

### Python モジュールのインポートエラー
```bash
# 仮想環境を使用している場合は有効化
source venv/bin/activate  # Mac/Linux
# または
venv\Scripts\activate  # Windows

# 依存関係を再インストール
pip3 install --upgrade -r requirements.txt
```
