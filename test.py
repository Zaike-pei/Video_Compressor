
import json
import subprocess
import unicodedata
import os
import protocol

# 動画ファイルの左右反転
#stream = ffmpeg.input('input/test.mp4').hflip().output('output/output.mp4')
#ffmpeg.run(stream)

# mp4ファイルから音声ファイルmp3の抽出 (ffmpeg-python)
#stream = ffmpeg.input('input/gopro.MP4').output('output/audio.mp3', format='mp3')
#ffmpeg.run(stream)

# mp4ファイルから音声ファイルmp3を抽出する(コマンド)

#cmd = 'ffmpeg -i input/cut_gopro.mp4 -ab 256k output/cut_gopro.mp3'



# 動画ファイルの情報を取得
# video_info = ffmpeg.probe('input/gopro.MP4')
# print(json.dumps(video_info, indent=2))

# video_stream = next((stream for stream in video_info['streams'] if stream['codec_type'] == 'video'), None)
# print('bitrate : '  + video_stream['bit_rate'])

# 動画から時間設定をした画像を取得
#ffmpeg.input('input/gopro.MP4', ss= 88).filter('scale', 500, -1).output('output/output.png', vframes=1).run()




# ファイル圧縮　crf（値が低いほど品質は向上する）
#cmd = 'ffmpeg -i input/cut_gopro.gif -crf 28 output/cut_gopro2.gif'
# subprocess.call(cmd.split())
# その他のコーデック
#cmd = 'ffmpeg -i input/test.mp4 -c:v libx264 -crf 28 output/test_comp_libx264_28.mp4'
#cmd = 'ffmpeg -i input/test.mp4 -c:v libx265 -crf 28 output/test_comp_libx265_28.mp4'
#cmd = 'ffmpeg -i input/test.mp4 -c:v libvpx-vp9 -crf 31 -b:v 0 output/test_comp_libprvx-vp9_31.mp4'

# 動画解像度の変更(width x height)
# 16:9
#cmd = 'ffmpeg -i input/test.mp4 -s 2560x1440 output/test_s2560x1440.mp4'
#cmd = 'ffmpeg -i input/test.mp4 -s 1920x1080 output/test_s1920x1080.mp4'
#cmd = 'ffmpeg -i input/test.mp4 -s 1600x900 output/test_s1600x900.mp4'
#cmd = 'ffmpeg -i input/test.mp4 -s 1280x720 output/test_s1280x720.mp4'
# 4:3
#cmd = 'ffmpeg -i input/test.mp4 -s 800x600 output/test_s800x600.mp4'
#cmd = 'ffmpeg -i input/test.mp4 -s 1024x768 output/test_s1024x768.mp4'
#cmd = 'ffmpeg -i input/test.mp4 -s 1280x960 output/test_s1280x960.mp4'
#cmd = 'ffmpeg -i input/test.mp4 -s 1600x1200 output/test_s1600x1200.mp4'
#cmd = 'ffmpeg -i input/test.mp4 -s 2048x1536 output/test_s2048x1536.mp4'
#cmd = 'ffmpeg -i input/test.mp4 -s 3200x2400 output/test_s3200x2400.mp4'



# アスペクト比を維持したままリサイズ
#cmd = 'ffmpeg -i input/test.mp4 -vf scale=720:-1 output/test_scale720:-1.mp4'
#cmd = 'ffmpeg -i input/test.mp4 -vf scale=-2:720 output/test_scale-1:720.mp4'
#cmd = 'ffmpeg -i input/test.mp4 -vf scale=1280:-1 output/test_scale1280:-1.mp4'
#cmd = 'ffmpeg -i input/test.mp4 -vf scale=-1:1280 output/test_scale-1:1280.mp4'

# アスペクト比の種類
#cmd = 'ffmpeg -i input/test.mp4 -aspect 4:3 output/test_asp4:3.mp4'
#cmd = 'ffmpeg -i input/test.mp4 -aspect 16:9 output/test_asp16:9.mp4'
#cmd = 'ffmpeg -i input/test.mp4 -aspect 9:16 output/test_asp9:16.mp4'
#cmd = 'ffmpeg -i input/test.mp4 -aspect 1:1 output/test_asp1:1.mp4'

# 指定した時間範囲でgifやwebmを作成
#cmd = 'ffmpeg -i input/cut_gopro.mp4 -ss 00:00:00 -to 00:00:05 -r 10 output/cut_gpro.gif'

# 動画から音声のみカット
#cmd = 'ffmpeg -i input/cut_gopro.mp4 -vcodec copy -an output/cut_gopro_au_cancel.mp4'

# 動画のカット処理
#cmd = 'ffmpeg -i input/gopro.MP4 -ss 00:00:00 -to 00:00:20 -c copy output/cut_gopro.mp4'
#cmd = 'ffmpeg -i input/cut_gopro.mp4 -ss 10 -t ２０ -c copy output/cut_gopro4.mp4'

#subprocess.call(cmd.split())


# s = unicodedata.normalize("NFKC", input())
# list = s.split(' ')
#print(unicodedata.normalize("NFKC", s))

# for num in list:
#     print(num)

# file_name = 'test.mp4'

# file, ext = os.path.splitext(file_name)
# print(file)

# print(ext)

# tmp = ext[1:]

# print(tmp)


# json_data = protocol.make_json("fdsafdsafdsafdafdsfsfsa", "mp4", 1, "hellooooooooooooooooooooooooo", '')
# type = 'mp4'
# content_size = 100000

# data = protocol.protocol_media_header(json_data, type, content_size)

# print(data)

# print(protocol.get_json_size(data))
# print(protocol.get_media_type_size(data))
# print(protocol.get_payload_size(data))

s = 'abcdefgabczzzz'
target = 'abc'

print(s[s.rfind(target) + len(target):])

# idx1 = s.find(target)
# idx2 = s.rfind(target)
# print(idx1)
# print(idx2)
# r = s[idx1+len(target):]

# print(r)

# print(json_data)
# print(len(json.dumps(json_data)))

# ljust_json = protocol.ljust_replace_space(json.dumps(json_data), json.dumps(json_data).encode('utf-8'), 100)
# print(len(ljust_json))

# back_json = json.loads(ljust_json)
# print(back_json)

# print(len(json.dumps(back_json)))

# json_data = {
#     "filename": content,
#     "content-type": content_madia_type,
#     "content-size": content_size,
#     "state-code": 1,
#     "error-message": ''
# }