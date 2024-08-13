import sys
import socket
import os
import unicodedata
import protocol
import json


class Tcp_client:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = 'localhost'
        self.server_port = 9001
        self.buffer_size = 32
        self.stream_rate = 1400
        self.state = 0

        self.path = '' # ファイルパス
        self.content = '' # ファイル名
        self.content_size = 0 # ファイルサイズ
        self.content_type = '' # メディアタイプ
    
    def start(self):
        try:
            self.sock.connect((self.server_address, self.server_port))
            print('connection server_address: {} server_port: {}'.format(self.server_address, self.server_port))

            # ファイル名とサイズの取得
            self.getFileInfo()

            # コマンドを作成
            command = self.createCommand()

            # jsonの作成とヘッダの作成
            json_data = protocol.make_json(self.content, self.content_type, 1, "", command)
            header = protocol.protocol_media_header(json_data, self.content_type, self.content_size)

            # ヘッダの送信
            self.sock.send(header)
            # サーバの応答受信
            response = self.sock.recv(self.buffer_size)
            print('[server]' + protocol.get_message(response))
            # サーバからヘッダ受信の旨のレスポンスを受け取ったら
            if protocol.get_state(response) == 1:
                # jsonファイルの送信
                self.sock.send(json_data.encode('utf-8'))
                # メディアタイプの送信
                self.sock.send(self.content_type.encode('utf-8'))
                # 動画データの送信
                self.uploadVideo()
                # 完了メッセージを受信
                recv_data = self.sock.recv(16)
                self.state = protocol.get_state(recv_data)
                print('[server]:' + protocol.get_message(recv_data))
                # 正常に動画を送信できた場合の処理
                if self.state == 1:
                    
                    print('ただいま動画ファイルをサーバーで処理しています。しばらくお待ちください。')
                     
                    
                else:
                    raise Exception
            
            else:
                raise Exception
            
            
        except socket.error as err:
            print('Socket_ERROR:' + str(err))
            print('プログラムを終了します')

        except Exception as err:
            print('ERROR:' + str(err))
            print('エラーが発生したためプログラムを終了します。')
            sys.exit(1)
        finally:
            print('closing socket')
            self.sock.close()


    # アップロードしたい動画ファイル名とサイズの取得
    def getFileInfo(self):
        while True:
            self.path = self.checkFileType()
            # ファイルサイズの確認
            if protocol.fileSize_Check(os.path.getsize(self.path)):
                self.content_size = os.path.getsize(self.path)
                break

    # ファイルの存在確認とmp4ファイルであるかの判定
    def checkFileType(self):
        temp = ''
        while True:
            self.content = input('type in mp4 file to upload to server:')
            path = 'input/' + self.content
            ext = os.path.splitext(path)[1]
            # ファイルが存在するかの確認
            if os.path.exists(path):
                # mp4ファイルであるかの確認
                if ext == '.mp4':
                    self.content_type = ext[1:]
                    temp = path
                    break
                else:
                    print('this is not mp4 file.')
            else:
                print('this file not exsits in input folder.')

        return temp
                
    # ffmpegのコマンドを作成
    def createCommand(self):
        # パスからファイル名を取得
        file, ext = os.path.splitext(self.content)
        cmd = 'ffmpeg -i temp/recv.mp4'
        # ナビゲーションによりコマンドを作成
        while True:
            process_code = unicodedata.normalize('NFKC', input('処理の選択を行います。\n1.圧縮\n2.解像度の変更 \n3.アスペクト比の変更 \n4.音声データ(mp3)の抽出\n' +
                                '5.GIFファイルの作成 \n6.指定した動画ファイルの情報を表示\n----------------------------------\n' +
                                '指定した動画に対して、行いたい処理を番号で入力してください: '))
            # 圧縮
            if process_code == '1':
                cmd += ' -crf 28 temp/comp_' + file + '.mp4'
                break
            # 解像度の変更
            elif process_code == '2':
                # 指定した解像度をコマンドに追加
                while True:
                    resolution_code = unicodedata.normalize('NFKC', input('適応したい解像度の選択を行います。\n16:9\n' +
                                            '1.WQHD  :2560x1440\n' +
                                            '2.FHD   :1920x1080\n' +
                                            '3.WXGA++:1600x900\n' +
                                            '4.HD    :1280x720\n' +
                                            '-------------------------\n' +
                                            '4:3\n' +
                                            '5.QUXGA   :3200x2400\n' +
                                            '6.QXGA    :2048x1536\n' +
                                            '7.UXGA    :1600x1200\n' +
                                            '8.QVGA    :1280x960\n' +
                                            '9.XGA     :1024x768\n' +
                                            '10.SVGA   :800x600\n' +
                                            '-------------------------\n' +
                                            '解像度を番号で入力してください:  '))
                    if resolution_code == '1':
                        cmd += ' -s 2560x1440 '
                        break
                    elif resolution_code == '2':
                        cmd += ' -s 1920x1080 '
                        break
                    elif resolution_code == '3':
                        cmd += ' -s 1600x900 '
                        break                    
                    elif resolution_code == '4':
                        cmd += ' -s 1280x720 '
                        break                   
                    elif resolution_code == '5':
                        cmd += ' -s 3200x2400 '
                        break                    
                    elif resolution_code == '6':
                        cmd += ' -s 2048x1536 '
                        break                    
                    elif resolution_code == '7':
                        cmd += ' -s 1600x1200 '
                        break                    
                    elif resolution_code == '8':
                        cmd += ' -s 1280x960 '
                        break                    
                    elif resolution_code == '9':
                        cmd += ' -s 1024x768 '
                        break                    
                    elif resolution_code == '10':
                        cmd += ' -s 800x600 '
                        break                    
                    else:
                        print('[error]適応させたい解像度の番号を入力してください。')
                        print('---------------------------------------------------------')    
                cmd += 'temp/changeQuality_' + file + '.mp4'
                print('解像度を決定しました')
                break
            # アスペクト比の変更
            elif process_code == '3':
                # 指定したアスペクト比をコマンドに追加
                while True:
                    aspect_code = unicodedata.normalize('NFKC', input('アスペクト比の選択を行います。（横:縦）\n1. 16:9\n2. 4:3\n3. 1:1\n4. 9:16\n' +
                                '適応したいアスペクト比の番号を入力してください: '))
                    if aspect_code == '1':
                        cmd += ' -aspect 16:9 '
                        break
                    elif aspect_code == '2':
                        cmd += ' -aspect 4:3 '
                        break
                    elif aspect_code == '3':
                        cmd += ' -aspect 1:1 '
                        break
                    elif aspect_code == '4':
                        cmd += ' -aspect 9:16 '
                        break                    
                    else:
                        print('[error]適応したいアスペクト比の番号で入力してください。')
                        print('-----------------------------------------------------------')
                cmd += 'temp/changeAspect_' + file + '.mp4'
                print('アスペクト比を決定しました')
                break
            #  音声データ(mp3)の抽出
            elif process_code == '4':
                cmd += ' -ab 256k temp/' + file + '.mp3'
                break
            # gif ファイルの作成
            elif process_code == '5':
                list = []
                while True:
                    print('gifファイルの作成を行います。')
                    sec = unicodedata.normalize('NFKC', input('開始地点(秒)と終了地点(秒)を半角スペース区切りの秒指定で指定してください。\n例)01:30 から 2:30 => 90 150\n' +
                                '入力してください：')).split(' ')


                    if sec[0].isdigit() and sec[1].isdigit():
                        list.append(sec[0])
                        list.append(sec[1])
                        break
                    else:
                        print('[error]開始地点の秒数と終了地点秒数をスペース区切で入力してください。')
                        print('--------------------------------------------------------------------------------')

                cmd += ' -ss ' + list[0] + ' -t ' + list[1] + ' -r 10 temp/' + file + '.gif'
                break
            # 動画ファイルの情報表示（未実装）
            elif process_code == '6':
                print('動画情報')
                print('動画情報........................')
            else:
                print('[error]行いたい処理の番号を入力してください。')
            print('-----------------------------------------')
        print('作成したコマンド: ' + cmd)
        return cmd
    
    # 動画データを読み込んでサーバに送信する
    def uploadVideo(self):
        with open(self.path, 'rb') as f:
            data = f.read(self.stream_rate)
            print('Sending...')
            while data:
                self.sock.send(data)
                data = f.read(self.stream_rate)
                
    




def main():
    tcp_client = Tcp_client()
    tcp_client.start()



if __name__ == '__main__':
    main()