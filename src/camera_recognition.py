import face_recognition
import cv2
import numpy as np
from switch_bot.find_by_uuid_and_press import run_bot_press
import time

def load_known_faces(image_paths):
    """既知の顔画像を読み込んで特徴量を抽出"""
    known_face_encodings = []
    known_face_names = []

    for i, path in enumerate(image_paths):
        image = face_recognition.load_image_file(path)
        face_locations = face_recognition.face_locations(image, model="hog")

        if len(face_locations) == 1:
            encoding = face_recognition.face_encodings(image, face_locations)[0]
            known_face_encodings.append(encoding)
            known_face_names.append(f"Person_{i+1}")
            print(f"✅ {path} の顔データを登録しました")
        else:
            print(f"⚠️  {path} から顔を検出できませんでした（検出数: {len(face_locations)}）")

    return known_face_encodings, known_face_names

def run_camera_recognition(known_face_encodings, known_face_names, tolerance=0.4):
    """カメラを使用したリアルタイム顔認証"""

    # カメラを起動（0は通常内蔵カメラ）
    video_capture = cv2.VideoCapture(0)

    if not video_capture.isOpened():
        print("❌ カメラを開けませんでした")
        return

    print("📷 カメラを起動しました。顔認証を開始します...")
    print("終了するには 'q' キーを押してください")

    # 処理を軽くするため、フレームをスキップ
    process_this_frame = True
    last_recognition_time = 0
    recognition_cooldown = 5  # 認証成功後5秒間は再認証しない

    # 変数の初期化
    face_locations = []
    face_names = []

    while True:
        # フレームを取得
        ret, frame = video_capture.read()

        if not ret:
            print("⚠️  フレームを取得できませんでした")
            break

        # 処理を軽くするため、2フレームに1回だけ処理
        if process_this_frame:
            # 画像を1/4サイズにリサイズして処理を高速化
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

            # BGRからRGBに変換（OpenCVはBGR、face_recognitionはRGBを使用）
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # 顔の位置を検出
            face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")

            # 検出された顔の特徴量を抽出
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            current_time = time.time()

            for face_encoding in face_encodings:
                # 既知の顔と比較
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=tolerance)
                name = "Unknown"

                # 最も近い顔を見つける
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index] and face_distances[best_match_index] < tolerance:
                        name = known_face_names[best_match_index]

                        # 認証成功時の処理（クールダウン考慮）
                        if current_time - last_recognition_time > recognition_cooldown:
                            print(f"🎉 顔認証成功: {name} (距離: {face_distances[best_match_index]:.3f})")

                            # SwitchBotを動作させる
                            try:
                                run_bot_press()
                                last_recognition_time = current_time
                            except Exception as e:
                                print(f"⚠️  SwitchBot制御エラー: {e}")

                face_names.append(name)

        process_this_frame = not process_this_frame

        # 結果を画面に表示
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # 座標を元のサイズに戻す
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            # 顔の周りに枠を描画
            if name != "Unknown":
                color = (0, 255, 0)  # 緑：認証成功
            else:
                color = (0, 0, 255)  # 赤：未認証

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # 名前を表示
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)

        # フレームを表示
        cv2.imshow('Face Recognition', frame)

        # 'q'キーで終了
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("👋 プログラムを終了します")
            break

    # 後処理
    video_capture.release()
    cv2.destroyAllWindows()

def main():
    """メイン処理"""
    # 登録する顔画像のパス
    known_face_paths = ["trainings/1.jpg", "trainings/2.jpg"]  # 必要に応じて複数の画像を追加可能

    print("🚀 顔認証システムを起動します...")

    # 既知の顔を読み込み
    known_face_encodings, known_face_names = load_known_faces(known_face_paths)

    if len(known_face_encodings) == 0:
        print("❌ 登録された顔がありません。train.jpg を確認してください。")
        return

    print(f"✅ {len(known_face_encodings)} 件の顔データを登録しました")

    # カメラ認証を開始
    run_camera_recognition(known_face_encodings, known_face_names, tolerance=0.4)

if __name__ == "__main__":
    main()
