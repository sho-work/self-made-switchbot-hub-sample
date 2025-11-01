#!/usr/bin/env python3
"""
FastAPIサーバーを単独で起動するスクリプト
"""

import os
import sys
import uvicorn

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    # trainingsディレクトリが存在しない場合は作成
    trainings_dir = os.path.join(project_root, "trainings")
    if not os.path.exists(trainings_dir):
        os.makedirs(trainings_dir)
        print(f"✅ trainingsディレクトリを作成しました: {trainings_dir}")
        print("⚠️  認証用の顔画像をtrainingsディレクトリに配置してください")

    # FastAPIサーバーを起動
    print("🚀 FastAPIサーバーを起動しています...")
    print("📝 APIドキュメント: http://localhost:8000/docs")
    print("🌐 Webアプリ用API: http://localhost:8000")
    print("")

    try:
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 サーバーを停止しました")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        sys.exit(1)