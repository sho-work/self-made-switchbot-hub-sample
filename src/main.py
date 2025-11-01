# ライブラリの読み込み
import face_recognition
import matplotlib.pyplot as plt
from switch_bot.find_by_uuid_and_press import run_bot_press

# 学習させたい（登録したい）顔画像のファイル名をリストに格納
train_img_names = ["train.jpg", ]
# 学習させた画像に対して、認証できるかテストに使う顔画像のファイル名をリストに格納
test_img_name = "test.jpg"

# 学習データの顔画像を読み込む
train_imgs = []
for name in train_img_names:
    train_img = face_recognition.load_image_file(name)
    train_imgs.append(train_img)

# テストデータ（認証する人の顔画像）を読み込む
test_img = face_recognition.load_image_file(test_img_name)

# 学習データの顔画像から顔の領域のみを検出する
train_img_locations = []
for img in train_imgs:
    # modelはhogとcnnを指定でき、cnnは重いが精度良い、hogは軽量だが精度は普通
    train_img_location = face_recognition.face_locations(img, model="hog")
    # 顔検出に失敗するとtrain_img_locationの長さは1となる
    # 顔検出に成功すると顔を検出し四角形で囲んだ四隅の座標を取得できる
    assert len(train_img_location) == 1, "画像から顔の検出に失敗したか、2人以上の顔が検出されました"
    train_img_locations.append(train_img_location)

# テストデータの顔画像から顔の領域のみを検出する
test_img_location = face_recognition.face_locations(test_img, model="hog")
assert len(test_img_location) == 1, "画像から顔の検出に失敗したか、2人以上の顔が検出されました"

# # 顔検出の結果を可視化する関数を定義
# def draw_img_locations(imgs, locations):
#     fig, ax = plt.subplots()
#     ax.imshow(imgs)
#     ax.set_axis_off()
#     for i, (top, right, bottom, left) in enumerate(locations):
#         # 四角形を描画する
#         w, h = right - left, bottom - top
#         ax.add_patch(plt.Rectangle((left, top), w, h, ec="r", lw=2, fill=None))
#     plt.show()

# # 学習データで顔検出した結果を可視化する
# for img, location in zip(train_imgs, train_img_locations):
#     draw_img_locations(img, location)

# # テストデータで顔検出した結果を可視化する
# draw_img_locations(test_img, test_img_location)

# 学習データの特徴量を抽出する
train_img_encodings = []
for img, location in zip(train_imgs, train_img_locations):
    (encoding, ) = face_recognition.face_encodings(img, location)
    train_img_encodings.append(encoding)

# テストデータの特徴量を抽出する
(test_img_encoding, ) = face_recognition.face_encodings(test_img, test_img_location)

# 学習データとテストデータの特徴量を比較し、ユークリッド距離を取得する
# 距離を見ることで顔がどれだけ似ているかわかる
dists = face_recognition.face_distance(train_img_encodings, test_img_encoding)

# 学習データとテストデータの距離が0.40以下のとき、顔が一致と判定
answer = False
for dist in dists:
    if dist < 0.40:
        answer = True

# 顔認証の結果を出力する
if answer:
    print("顔認証に成功しました🎉")
    run_bot_press()
else:
    print("顔認証に失敗しました🙅")
