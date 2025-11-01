#!/bin/bash

# エラーハンドリングを有効化
set -e

# プロジェクトルートディレクトリを取得
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 色付き出力のための定数
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ログ出力関数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Pythonの確認
if ! command -v python3 &> /dev/null; then
    log_error "Python3が見つかりません。Pythonをインストールしてください。"
    exit 1
fi

# Node.jsの確認
if ! command -v node &> /dev/null; then
    log_error "Node.jsが見つかりません。Node.jsをインストールしてください。"
    exit 1
fi

# 依存関係のインストール確認
log_info "Python依存関係を確認しています..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    log_warning "Python依存関係がインストールされていません。インストールしています..."
    pip3 install -r requirements.txt || {
        log_error "Python依存関係のインストールに失敗しました"
        exit 1
    }
fi

# trainingsディレクトリの確認
if [ ! -d "trainings" ]; then
    log_warning "trainingsディレクトリが存在しません。作成しています..."
    mkdir -p trainings
    log_info "trainingsディレクトリを作成しました。認証用の顔画像を配置してください。"
fi

# FastAPIサーバーを起動
log_info "FastAPIサーバーを起動しています..."
cd "$PROJECT_ROOT/api"
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

# FastAPIサーバーの起動を待つ
log_info "FastAPIサーバーの起動を待っています..."
for i in {1..10}; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        log_info "FastAPIサーバーが起動しました！"
        break
    fi
    if [ $i -eq 10 ]; then
        log_error "FastAPIサーバーの起動に失敗しました"
        kill $API_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Node.js依存関係のインストール
cd "$PROJECT_ROOT/web"
if [ ! -d "node_modules" ]; then
    log_info "Node.js依存関係をインストールしています..."
    npm install || {
        log_error "Node.js依存関係のインストールに失敗しました"
        kill $API_PID 2>/dev/null
        exit 1
    }
fi

# Vite開発サーバーを起動
log_info "Vite開発サーバーを起動しています..."
npm run dev &
WEB_PID=$!

# 起動メッセージ
sleep 2
echo ""
echo "========================================"
echo -e "${GREEN}サーバーが正常に起動しました！${NC}"
echo "========================================"
echo "FastAPI: http://localhost:8000"
echo "FastAPI Docs: http://localhost:8000/docs"
echo "Web App: http://localhost:3000"
echo "========================================"
echo ""
echo "終了するには Ctrl+C を押してください"
echo ""

# Ctrl+Cで両方のプロセスを終了
cleanup() {
    echo ""
    log_info "サーバーを停止しています..."
    kill $API_PID $WEB_PID 2>/dev/null
    log_info "サーバーを停止しました"
    exit 0
}

trap cleanup INT
wait