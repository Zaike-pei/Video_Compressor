import socket
import os
import unicodedata
import protocol
import json
import time
import threading


class Tcp_client:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = 'localhost'
        self.server_port = 9001
        self.header_buffer_size = 32
        self.response_buffer_size = 16
        self.stream_rate = 1400
        self.state = 0

        self.path = '' # ファイルパス
        self.content = '' # ファイル名
        self.content_size = 0 # ファイルサイズ
        self.content_type = '' # メディアタイプ
        self.json_data = '' # 整形後のjsonを格納
    
    def start(self):
        try:
            # inputディレクトリの作成
            if not os.path.exists('input'):
                print('inputディレクトリを作成しました、mp4データをインプットフォルダーに準備して下さい。')
                os.makedirs('input')
            
            # outputディレクトリの作成 
            if not os.path.exists('output'):
                os.makedirs('output')

            self.sock.connect((self.server_address, self.server_port))
            print('connection server_address: {} server_port: {}'.format(self.server_address, self.server_port))

            # ファイル名とサイズの取得
            self._getFileInfo()
            # コマンドを作成
            command = self._createCommand()
            # 終了選択の場合
            if command == '':
                raise Exception('プログラムを終了します。')
            # jsonの作成とヘッダの作成
            self.json_data = protocol.make_json(self.content, self.content_type, 1, "", command)
            header = protocol.protocol_media_header(self.json_data, self.content_type, self.content_size)
            # ヘッダの送信
            self.sock.send(header)
            # サーバの応答受信
            response = self.sock.recv(self.header_buffer_size)
            print('[server]:' + protocol.get_message(response))

            # ヘッダー受信段階でエラー
            if protocol.get_state(response) != 1:
                raise Exception('ヘッダー送信段階でエラーが発生しました。')

            # データの送信
            self._uploadData(self.json_data)
            # 完了メッセージを受信
            response = self.sock.recv(self.response_buffer_size)
            self.state = protocol.get_state(response)
            print('[server]:' + protocol.get_message(response))

            # 動画アップロード段階でエラーコード
            if self.state != 1:
                raise Exception('データ送信段階でエラーが発生しました。')
            
            # 動画編集終了まで待機
            resultCode = self._wait_response_loop(self.sock)

            # サーバーからエラーコード受信
            if resultCode != 1:
                raise Exception('サーバーで編集処理中にエラーが発生しました。')
            
            # ヘッダーの受信
            header = self.sock.recv(self.header_buffer_size)

            # ヘッダー受信エラー
            if header == b'':
                self.sock.send(protocol.response_protocol(2, 'can`t reciev'))
                raise Exception('ヘッダーの受信ができませんでした。')
            
            # ヘッダ取得完了のレスポンスを返す
            self.sock.send(protocol.response_protocol(1, 'recieved header'))

            # データサイズをヘッダから取得
            json_size = protocol.get_json_size(header)
            media_type_size = protocol.get_media_type_size(header)
            self.content_size = protocol.get_payload_size(header) 

            # データを受信
            self._receivData(self.sock, json_size, media_type_size)

            # データ受信段階でエラーコード受信
            if self.state != 1:
                self.sock.send(protocol.response_protocol(2, 'failed upload'))
                raise Exception('データダウンロード段階でエラーが発生しました。')
            
            self.sock.send(protocol.response_protocol(1, 'completed'))

            print('正常にプログラムが実行されました。プログラムを終了します。')
                         
        except socket.error as err:
            print('Socket_ERROR:' + str(err))
            print('プログラムを終了します')
        except Exception as err:
            print('\nERROR:' + str(err))
        finally:
            print('closing socket')
            self.sock.close()


    # 動画ファイル名とサイズの取得
    def _getFileInfo(self) -> None:
        while True:
            self.path = self._checkFileType()
            # ファイルサイズの確認
            if protocol.fileSize_Check(os.path.getsize(self.path)):
                self.content_size = os.path.getsize(self.path)
                break

    # ファイルの存在確認とmp4ファイルであるかの判定
    def _checkFileType(self) -> str:
        temp = ''
        while True:
            print('-----------------------------------------------')
            try:   
                self.content = self._input_with_timeout('If you want to quit the process, type "exit".\ntype in mp4 file to upload to server:', timeout=30)
            except TimeoutError as err:
                raise Exception("タイムアウトエラーが発生しました。")
            # 処理を終了の場合
            if self.content == 'exit':
                raise Exception('プログラムを終了します。')
            
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

    # タイムアウト付き標準入力
    def _input_with_timeout(self, prompt, timeout=10):
        self.input_result = None

        def get_input():
            self.input_result = input(prompt)

        input_thread = threading.Thread(target=get_input)
        input_thread.deamon = True
        input_thread.start()

        input_thread.join(timeout)

        if self.input_result is None:
            raise TimeoutError("入力がタイムアウトしました。")
        
        return self.input_result

    # ffmpegのコマンドを作成
    def _createCommand(self) -> str:
        # パスからファイル名を取得
        cmd = 'ffmpeg -i temp/input.mp4'
        # ナビゲーションによりコマンドを作成
        while True:
            process_code = unicodedata.normalize('NFKC', input('処理の選択をして下さい。\n1.圧縮\n2.解像度の変更 \n3.アスペクト比の変更 \n4.音声データ(mp3)の抽出\n' +
                                '5.GIFファイルの作成 \n6.動画の指定秒数切り取り\n7.指定した動画ファイルの情報を表示（未実装）\n8.終了\n----------------------------------\n' +
                                '指定した動画に対して、行いたい処理を番号で入力してください: '))
            # 圧縮
            if process_code == '1':
                cmd += ' -crf 28 temp/comp_output.mp4'
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
                cmd += 'temp/changeQuality_output.mp4'
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
                cmd += 'temp/changeAspect_output.mp4'
                print('アスペクト比を決定しました')
                break
            #  音声データ(mp3)の抽出
            elif process_code == '4':
                cmd += ' -ab 256k temp/output.mp3'
                break
            # gif ファイルの作成
            elif process_code == '5':
                list = []
                while True:
                    print('gifファイルの作成を行います。')
                    sec = unicodedata.normalize('NFKC', input('開始地点(秒)と終了地点(秒)を半角スペース区切りの秒指定で入力してください。\n例)01:30 から 2:30 => 90 150\n' +
                                '入力：')).split(' ')
                    if sec[0].isdigit() and sec[1].isdigit():
                        list.append(sec[0])
                        list.append(sec[1])
                        break
                    else:
                        print('[error]開始地点の秒数と終了地点秒数をスペース区切で入力してください。')
                        print('--------------------------------------------------------------------------------')

                cmd += ' -ss ' + list[0] + ' -t ' + list[1] + ' -r 10 temp/output.gif'
                break
            # 動画の切り取り
            elif process_code == '6':
                list = []
                while True:
                    print('動画の切り取り処理に移行します。')
                    sec = unicodedata.normalize('NFKC', input('開始地点（秒）と終了地点（秒）を半角スペース区切りの秒指定で入力して下さい。\n例)01:30 から 2:30 => 90 150\n' +
                                                              '入力：')).split(' ')
                    if sec[0].isdigit() and sec[1].isdigit():
                        for s in sec:
                            list.append(s)
                        break
                    else:
                        print('[error]開始地点の秒数と終了地点秒数をスペース区切で入力してください。')
                        print('--------------------------------------------------------------------------------')
                
                cmd += ' -ss ' + list[0] + ' -t ' + list[1] + ' temp/cut_output.mp4'
                break       
            # 動画ファイルの情報表示（未実装）
            elif process_code == '7':
                print('動画情報')
                print('動画情報........................')
            # 終了
            elif process_code == '8':
                cmd = ''
                return cmd
            else:
                print('[error]行いたい処理の番号を入力してください。')
            print('-----------------------------------------')

        return cmd
    
    # データをサーバに送信する
    def _uploadData(self, json: dict) -> None:
        # jsonデータの送信
        self.sock.send(json.encode('utf-8'))
        # メディアタイプの送信
        self.sock.send(self.content_type.encode('utf-8'))
        # 動画データの送信
        with open(self.path, 'rb') as f:
            data = f.read(self.stream_rate)
            print('指定した動画データの送信を開始します。')
            print('Sending...')
            while data:
                self.sock.send(data)
                data = f.read(self.stream_rate)

    # 待機用受信ループ
    def _wait_response_loop(self, con: socket) -> int:
        print('ただいま動画ファイルをサーバーで処理しています。しばらくお待ちください。')

        while True:
            recv_data = con.recv(16)
            state = protocol.get_state(recv_data)
            message = protocol.get_message(recv_data)
            print(f'[server]:{message}')
            if state != 0:
                break
            
            time.sleep(10)
        return state

    # データ受信処理
    def _receivData(self, con: socket, json_size: int, media_type_size: int) -> None:
        # jsonデータの受信
        byte_json_data = protocol.remove_padding(con.recv(json_size))
        self.json_data = json.loads(byte_json_data.decode('utf-8'))
        # メディアタイプデータの受信
        self.content_type = con.recv(media_type_size)
        # ダウンロードデータのファイル名を取得
        filename = self.json_data["file_name"]

        # 動画データを受信
        flag = True # 判定用の変数
        with open('output/comp_' + filename, 'wb+') as f:
            while self.content_size > 0:
                data = con.recv(self.content_size if self.content_size <= self.stream_rate else self.stream_rate)
                f.write(data)
                self.content_size -= len(data)
                # 受信するべきデータがまだ残っている且つ受信データが無い場合処理中断
                if len(data) == 0 and self.content_size > 0:
                    print('接続の問題によりクライアントからの受信データがないため受信待ちを終了します。')
                    flag = False
                    break
        # ダウンロード結果をフラッグで判定
        if flag:
            print('Finished download the file from server')
            self.state = 1
        else:
            print('動画ダウンロード中にエラーが発生しました。')
            self.state = 2


def main():
    tcp_client = Tcp_client()
    tcp_client.start()


if __name__ == '__main__':
    main()