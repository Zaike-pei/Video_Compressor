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
                        self.data_size = int.from_bytes(header, 'big')
                        # 動画データを受信
                        self.recievData(connection, dpath)
                        # 受信終了後メッセージの送信
                        response = ''
                        if self.state == 1:
                            response = protocol.response_protocol(self.state, 'recieved data')
                        else:
                            response = protocol.response_protocol(self.state, 'failed')
                            
                        connection.send(response)





                        # jsonの作成
                        json_data = {
                            "filename": self.content,
                            "content-type": self.content_madia_type,
                            "content-size": self.content_size
                        }

                    break

                    # テスト用
                    # json_data = connection.recv(19).decode('utf-8')
                    # print(len(json_data))
                    # json_data += connection.recv(1).decode('utf-8')
                    # print(json.dumps(json.loads(json_data), indent=4))
                    # data = {
                    #     "name": 'hinako',
                    #     "age": 3
                    # }
                    # connection.send(json.dumps(data).encode('utf-8'))
                    #break
                    
            except Exception as err:
                print('[TCP]Error:' + str(err))
            finally:
                print('[TCP]closing socket')
                connection.close()

    # 動画データを受信し、tempフォルダー内に新しい動画ファイルを作成する
    def recievData(self, con, path):
        with open(os.path.join(path, 'recv.mp4'), 'wb+') as f:
            while self.data_size > 0:
                data = con.recv(self.data_size if self.data_size <= self.stream_rate else self.stream_rate)
                f.write(data)
                print('recieved {} bytes'.format(len(data)))
                self.data_size -= len(data)
                print('rest bytes:' + str(self.data_size) + ' bytes')

            print('Finished download the file from client')
            self.state = 1
        

        

    
    # def json_test(self):
    #     print('hello')

def main():
    tcp = Tcp_server()

    # tcpサーバー起動
    thread1 = threading.Thread(target=tcp.start)

    thread1.start()

if __name__ == '__main__':
    main()