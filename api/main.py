from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import face_recognition
import numpy as np
import cv2
import asyncio
import sys
import os
from typing import Optional, List
import base64
from io import BytesIO
from PIL import Image

# srcディレクトリをパスに追加
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if os.path.exists(src_path):
    sys.path.insert(0, src_path)

# switch_botのインポート（エラー処理付き）
try:
    from switch_bot.find_by_uuid_and_press import main as switch_bot_main
    SWITCH_BOT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  SwitchBotモジュールのインポートエラー: {e}")
    SWITCH_BOT_AVAILABLE = False

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# グローバル変数として既知の顔を保存
known_face_encodings = []
known_face_names = []

class FaceRecognitionRequest(BaseModel):
    image_data: str  # Base64エンコードされた画像データ

class FaceRecognitionResponse(BaseModel):
    success: bool
    recognized: bool
    name: Optional[str] = None
    confidence: Optional[float] = None
    message: str

class SwitchBotRequest(BaseModel):
    action: str = "press"

class StatusResponse(BaseModel):
    status: str
    known_faces_count: int

def load_known_faces():
    """起動時に既知の顔画像を読み込み"""
    global known_face_encodings, known_face_names

    # trainingsディレクトリから画像を読み込み
    training_dir = os.path.join(os.path.dirname(__file__), '..', 'trainings')

    if not os.path.exists(training_dir):
        print(f"⚠️  {training_dir} が存在しません")
        return

    image_files = [f for f in os.listdir(training_dir)
                  if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    for i, filename in enumerate(image_files):
        path = os.path.join(training_dir, filename)
        try:
            image = face_recognition.load_image_file(path)
            face_locations = face_recognition.face_locations(image, model="hog")

            if len(face_locations) == 1:
                encoding = face_recognition.face_encodings(image, face_locations)[0]
                known_face_encodings.append(encoding)
                name = os.path.splitext(filename)[0]  # ファイル名を名前として使用
                known_face_names.append(name)
                print(f"✅ {filename} の顔データを登録しました")
            else:
                print(f"⚠️  {filename} から顔を検出できませんでした")
        except Exception as e:
            print(f"❌ {filename} の読み込みエラー: {e}")

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    print("🚀 FastAPI サーバーを起動します...")
    load_known_faces()
    print(f"✅ {len(known_face_encodings)} 件の顔データを登録しました")

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {"message": "Face Recognition API Server"}

@app.get("/status")
async def get_status():
    """サーバーステータスの取得"""
    return StatusResponse(
        status="running",
        known_faces_count=len(known_face_encodings)
    )

@app.post("/api/face_recognition")
async def recognize_face(request: FaceRecognitionRequest):
    """顔認証エンドポイント"""
    try:
        # Base64デコード
        image_data = base64.b64decode(request.image_data.split(',')[1] if ',' in request.image_data else request.image_data)

        # PILで画像を開く
        image = Image.open(BytesIO(image_data))

        # RGB形式に変換
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # numpy配列に変換
        image_np = np.array(image)

        # 顔の検出と特徴量抽出
        face_locations = face_recognition.face_locations(image_np, model="hog")

        if len(face_locations) == 0:
            return FaceRecognitionResponse(
                success=True,
                recognized=False,
                message="顔が検出されませんでした"
            )

        face_encodings = face_recognition.face_encodings(image_np, face_locations)

        for face_encoding in face_encodings:
            # 既知の顔と比較
            tolerance = 0.4
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=tolerance)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index] and face_distances[best_match_index] < tolerance:
                    name = known_face_names[best_match_index]
                    confidence = float(1 - face_distances[best_match_index])

                    # 認証成功時、自動的にSwitchBotを動作
                    if SWITCH_BOT_AVAILABLE:
                        try:
                            await switch_bot_main()
                            message = f"顔認証成功: {name} - SwitchBotを動作させました"
                        except Exception as e:
                            message = f"顔認証成功: {name} - SwitchBot動作エラー: {str(e)}"
                    else:
                        message = f"顔認証成功: {name} - SwitchBot機能は利用できません"

                    return FaceRecognitionResponse(
                        success=True,
                        recognized=True,
                        name=name,
                        confidence=confidence,
                        message=message
                    )

        return FaceRecognitionResponse(
            success=True,
            recognized=False,
            message="登録されていない顔です"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/switch_bot/press")
async def switch_bot_press(request: SwitchBotRequest):
    """SwitchBot制御エンドポイント"""
    try:
        if request.action != "press":
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "サポートされていないアクションです"}
            )

        if not SWITCH_BOT_AVAILABLE:
            return JSONResponse(
                status_code=503,
                content={"success": False, "message": "SwitchBot機能は利用できません"}
            )

        # SwitchBotを動作
        await switch_bot_main()

        return JSONResponse(
            content={"success": True, "message": "SwitchBotを動作させました"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload_known_face")
async def upload_known_face(file: UploadFile = File(...), name: str = ""):
    """既知の顔画像をアップロード"""
    try:
        # ファイルを保存
        training_dir = os.path.join(os.path.dirname(__file__), '..', 'trainings')
        os.makedirs(training_dir, exist_ok=True)

        filename = name if name else file.filename
        if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            filename += '.jpg'

        file_path = os.path.join(training_dir, filename)

        contents = await file.read()
        with open(file_path, 'wb') as f:
            f.write(contents)

        # 顔画像を登録
        image = face_recognition.load_image_file(file_path)
        face_locations = face_recognition.face_locations(image, model="hog")

        if len(face_locations) != 1:
            os.remove(file_path)  # 失敗したら削除
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": f"顔が検出できませんでした（検出数: {len(face_locations)}）"}
            )

        encoding = face_recognition.face_encodings(image, face_locations)[0]
        known_face_encodings.append(encoding)
        known_face_names.append(os.path.splitext(filename)[0])

        return JSONResponse(
            content={"success": True, "message": f"顔データを登録しました: {filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)