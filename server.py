import sys
import socket
import threading
import time
import datetime
import os
import json
import protocol


class Tcp_server:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = '0.0.0.0'
        self.server_port = 9001
        self.buffer_size = 32
        self.stream_rate = 1400

        self.data_size = 0
        self.state = 0

        self.sock.bind((self.server_address, self.server_port))
        print('[TCP]Starting up on {} port {}'.format(self.server_address,self.server_port))
        self.sock.listen(1)
    
    def start(self):
        # ダウンロード済みの動画を保存するディレクトリの作成
        dpath = 'temp'
        if not os.path.exists(dpath):
            os.makedirs(dpath)

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

                        print('json_size: ' + str(json_size) + ' bytes')
                        print('media_type_size: ' + str(media_type_size) + ' bytes')
                        print('payload_size: ' + str(self.data_size) + ' bytes')
                        # ヘッダ取得完了のレスポンスを返す
                        connection.send(protocol.response_protocol(self.state, 'recieved header'))

                        # jsonデータの受信
                        json_data = connection.recv(json_size)
                        print(json.loads(json_data.decode('utf-8')))
                        # メディアタイプデータの受信
                        media_type = connection.recv(media_type_size)
                        print(media_type.decode('utf-8'))
                        # エラースロー
                        #raise Exception

                        # 動画データを受信
                        self.recievData(connection, dpath)
                        # 受信終了後メッセージの送信
                        response = ''
                        if self.state == 1:
                            response = protocol.response_protocol(self.state, 'recieved data')
                        else:
                            response = protocol.response_protocol(self.state, 'failed upload')
                            
                        connection.send(response)
                        print('hello')

                        # ステートがエラーだった場合処理終了

                    else:
                        self.state = 0
                        connection.send(protocol.response_protocol(self.state, 'error'))

                    break
                    
            except Exception as err:
                print('[TCP]Error:' + str(err))
            finally:
                print('[TCP]closing socket')
                connection.close()


    # 動画データを受信し、tempフォルダー内に新しい動画ファイルを作成する
    def recievData(self, con, path):
        flag = True
        with open(os.path.join(path, 'recv.mp4'), 'wb+') as f:
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
            
        

def main():
    tcp = Tcp_server()

    # tcpサーバー起動
    thread1 = threading.Thread(target=tcp.start)

    thread1.start()

if __name__ == '__main__':
    main()