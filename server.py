import sys
import socket
import threading
import time
import datetime
import os
import json
import protocol
import subprocess
import asyncio


class Tcp_server:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = '0.0.0.0'
        self.server_port = 9001
        self.buffer_size = 32
        self.stream_rate = 1400

        self.data_size = 0
        self.state = 0

        self.media_type = ''
        self.json_data = ''

        self.sock.bind((self.server_address, self.server_port))
        print('[TCP]Starting up on {} port {}'.format(self.server_address,self.server_port))
        self.sock.listen(1)
    
    def start_thread(self):
        asyncio.run(self.start_server())

    async def start_server(self):
        # ダウンロード済みの動画を保存するディレクトリの作成
        if not os.path.exists('temp'):
            os.makedirs('temp')

        while True:
            connection, address = self.sock.accept()
            
            try:
                while True:
                    t_delta = datetime.timedelta(hours=9)
                    jst = datetime.timezone(t_delta, 'JST')
                    now = datetime.datetime.now(jst)
                    print('[TCP]connecting from {} {}'.format(address, now.strftime('%Y/%m/%d %H:%M:%S')))

                    #ヘッダデータを受信
                    header = connection.recv(self.buffer_size)
                    if header != 0:
                        self.state = 1
                        # jsonサイズ、メディアタイプサイズ、ペイロードサイズのをヘッダから取得
                        json_size = protocol.get_json_size(header)
                        media_type_size = protocol.get_media_type_size(header)
                        self.data_size = protocol.get_payload_size(header)

                        # ヘッダ取得完了のレスポンスを返す
                        connection.send(protocol.response_protocol(self.state, 'recieved header'))

                        # データを受信
                        self.recievData(connection, json_size, media_type_size)

                        # 受信終了後メッセージの送信
                        response = ''
                        if self.state == 1:
                            response = protocol.response_protocol(self.state, 'recieved data')
                            connection.send(response)

                            # jsonデータを展開
                            # self.json_data = json.loads(self.json_data.decode('utf-8'))
                            # fname = self.json_data['filename']
                            # con_type = self.json_data['content-type']
                            # state = self.json_data['state']
                            command = self.json_data['command']
                            print(command)

                            # 動画編集とクライアントへのメッセージ送信
                            tasks = [asyncio.create_task(self.video_Editing(command)), asyncio.create_task(self.wait_loop())]
                            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)


                            print('動画編集処理完了')
                            
                        else:
                            response = protocol.response_protocol(self.state, 'failed upload')
                            connection.send(response)
                            

                        break

                        # ステートがエラーだった場合処理終了
                    # ヘッダ情報を受信できなかった場合のエラー
                    else:
                        self.state = 0
                        connection.send(protocol.response_protocol(self.state, 'error'))
                        raise Exception

                    
            except Exception as err:
                print('[TCP]Error:' + str(err))
            finally:
                print('[TCP]closing socket')
                connection.close()


    # 動画データを受信し、tempフォルダー内に新しい動画ファイルを作成する
    def recievData(self, con, json_size, media_type_size):
        # jsonデータの受信
        json_data = con.recv(json_size)
        self.json_data = json.loads(json_data.decode('utf-8'))
        #print(json.loads(self.json_data.decode('utf-8')))
        # メディアタイプデータの受信
        self.media_type = con.recv(media_type_size)
        #print(self.media_type.decode('utf-8'))
        # 動画データにダウンロード
        flag = True
        with open('temp/recv.mp4', 'wb+') as f:
            while self.data_size > 0:
                data = con.recv(self.data_size if self.data_size <= self.stream_rate else self.stream_rate)
                f.write(data)
                #print('recieved {} bytes'.format(len(data)))
                self.data_size -= len(data)
                #print('rest bytes:' + str(self.data_size) + ' bytes')

                # 受信するべきデータがまだ残っている且つ受信データが無い場合処理中断
                if len(data) == 0 and self.data_size > 0:
                    print('接続の問題によりクライアントからの受信データがないため受信待ちを終了します。')
                    flag = False
                    break

        if flag:
            print('Finished download the file from client')
            self.state = 1
        else:
            print('動画ダウンロード中にエラーが発生しました。')
            self.state = 0
            
    # 動画ファイル編集
    async def video_Editing(self, command):
        # 圧縮後のファイル名取得
        target = 'temp/'
        filename = command[command.rfind(target) + len(target):]
        print('編集後のファイル名： ' + str(filename))

        print('動画編集を開始')
        # 動画データの編集（ffmpeg）
        await subprocess.call(command.split())
        print('動画編集終了')

        print('コマンド実行完了')

        
    # 処理待機用関数
    async def wait_loop(self):
        while True:
            print('動画処理の終了待機します。')
            await asyncio.sleep(5)
            print('待機完了')



def main():
    tcp = Tcp_server()

    # tcpサーバー起動
    thread1 = threading.Thread(target=tcp.start_thread)
    thread1.start()


if __name__ == '__main__':
    main()