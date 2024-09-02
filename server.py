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
        self.header_buffer_size = 32
        self.response_buffer_size = 16
        self.stream_rate = 1400

        self.data_size = 0
        self.state = 0
        self.media_type = ''
        self.json_data = ''
        self.fileName = ''

        self.sock.bind((self.server_address, self.server_port))
        print('[TCP]Starting up on {} port {}'.format(self.server_address,self.server_port))
        self.sock.listen(1)
    

    def start_thread(self):
        asyncio.run(self._start_server())

    async def _start_server(self):
        # ダウンロード済みの動画を保存するディレクトリの作成
        if not os.path.exists('temp'):
            os.makedirs('temp')

        while True:
            print('[TCP]Waiting for connection...')
            connection, address = self.sock.accept()
            
            try:
                while True:
                    t_delta = datetime.timedelta(hours=9)
                    jst = datetime.timezone(t_delta, 'JST')
                    now = datetime.datetime.now(jst)
                    print('[TCP]connecting from {} {}'.format(address, now.strftime('%Y/%m/%d %H:%M:%S')))

                    #ヘッダデータを受信
                    header = connection.recv(self.header_buffer_size)

                    # ヘッダデータ取得失敗だった場合
                    if header == b'':
                        connection.send(protocol.response_protocol(2, 'error'))
                        raise Exception('ヘッダー受信シーケンスでエラーが発生しました。')
                    
                    # ヘッダ取得完了のレスポンスを返す
                    connection.send(protocol.response_protocol(1, 'recieved header'))
                    
                    # データサイズをヘッダから取得
                    json_size = protocol.get_json_size(header)
                    media_type_size = protocol.get_media_type_size(header)
                    self.data_size = protocol.get_payload_size(header)
                    # データを受信
                    self._recievData(connection, json_size, media_type_size)

                    # データ取得失敗だった場合
                    if self.state != 1:
                        connection.send(protocol.response_protocol(2, 'failed upload'))
                        raise Exception('データ受信シーケンスでエラーが発生しました。')
                    
                    # データ取得完了のレスポンスを返す  
                    connection.send(protocol.response_protocol(1, 'recieved data'))

                    # 動画編集とクライアントへのメッセージ送信
                    tasks = [asyncio.create_task(self._video_Editing(self.json_data['command'])), asyncio.create_task(self._send_message_loop(connection))]
                    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    # 結果をレスポンスする
                    for task in done:
                        # 動画編集処理失敗だった場合 
                        if task.result() != 0:
                            connection.send(protocol.response_protocol(2, 'error'))
                            raise Exception('動画編集シーケンスでエラーが発生しました。')
                        # 編集完了のレスポンスを送信
                        connection.send(protocol.response_protocol(1, 'done'))

                    # タスクのキャンセル
                    for task in tasks:
                        task.cancel()

                    # 編集前の動画ファイルを削除
                    self._removeSpecifyData(self.fileName)
                    # 編集後のファイル名取得
                    self.fileName = self._getEditedFileName(self.json_data['command'])
                    # 送信するファイルのサイズとメディアタイプ情報を設定
                    self._setFileInfo(self.fileName)
                    # jsonの作成
                    json_data = protocol.make_json(self.fileName, self.media_type, 1, '', '')
                    # ヘッダの作成
                    header = protocol.protocol_media_header(json_data, self.media_type, self.data_size)
                    #　ヘッダーの送信
                    connection.send(header)
                    # クライアントの応答受信
                    response = connection.recv(self.response_buffer_size)

                    print(f'[Client]{protocol.get_message(response)}')

                    # ヘッダーデータ送信失敗だった場合
                    if protocol.get_state(response) != 1:
                        raise Exception('ヘッダー送信シーケンスでエラーが発生しました。')
                    
                    # データを送信
                    self._uploadData(connection, self.fileName, json_data)

                    # クライアントがデータを受信できたかの確認をするレスポンスを受け取る
                    response = connection.recv(self.response_buffer_size)

                    # クライアント側でダウンロードエラーがあった場合
                    if protocol.get_state(response) != 1:
                        print('クライアントがデータ受信段階においてエラーが発生しています。')
                        raise Exception('クライアント側で受信エラーが発生しました。接続を閉じます。')
                    
                    # サーバーにダウンロードしたファイルを削除する
                    self._removeSpecifyData(self.fileName)

                    print('[TCP]disconnecting from {} {}'.format(address, now.strftime('%Y/%m/%d %H:%M:%S')))

                    break

                   

            except Exception as err:
                print(f'[TCP]Error: {str(err)}')
            finally:
                print('[TCP]closing socket')
                connection.close()


    # データ受信処理
    def _recievData(self, con: socket, json_size: int, media_type_size: int) -> None:
        # jsonデータの受信
        json_data = protocol.remove_padding(con.recv(json_size))
        self.json_data = json.loads(json_data.decode('utf-8'))
        # ファイル名の取得とコマンドのファイル名項の書き換え
        self.fileName = self._getFileName(self.json_data)
        # メディアタイプデータの受信
        self.media_type = con.recv(media_type_size)

        # 動画データをダウンロード
        flag = True
        with open('temp/' + self.fileName, 'wb+') as f:
            while self.data_size > 0:
                data = con.recv(self.data_size if self.data_size <= self.stream_rate else self.stream_rate)
                f.write(data)
                self.data_size -= len(data)

                # 受信するべきデータがまだ残っている且つ受信データが無い場合処理中断
                if len(data) == 0 and self.data_size > 0:
                    print('接続の問題によりクライアントからの受信データがないため受信待ちを終了します。')
                    flag = False
                    break

        # ダウンロード結果をフラッグで判定
        if flag:
            print('Finished download the file from client')
            self.state = 1
        else:
            print('動画ダウンロード中にエラーが発生しました。')
            self.state = 0
            
    # データ送信
    def _uploadData(self, con: socket, filename: str, json: str) -> None:
        # jsonデータの送信
        con.send(protocol.ljust_replace_padding(json ,100))
        # メディアタイプの送信
        con.send(self.media_type.encode('utf-8'))
        # 動画データの送信
        with open('temp/' + filename, 'rb') as f:
            data = f.read(self.stream_rate)
            print('指定した動画データの送信を開始します。')
            print('Sending...')
            while data:
                con.send(data)
                data = f.read(self.stream_rate)

    # 動画ファイル編集（ffmpeg）
    async def _video_Editing(self, command:str) -> int:
        # サブプロセス実行
        print('動画データの編集を開始します。')
        proc = await asyncio.create_subprocess_exec(
            *command.split(' '),
            stdout = asyncio.subprocess.PIPE, # 標準出力のキャプチャ用
            stderr= asyncio.subprocess.PIPE  # 標準エラー出力のキャプチャ用
        )
        # バッファリング防止
        await proc.communicate()
        # サブプロセスの終了コードを取得
        returncode = await proc.wait()
        print('動画データ編集処理終了')

        return returncode
  
    # 処理待機用関数
    async def _send_message_loop(self, con: socket) -> None:
        while True:
            print('動画編集中...')
            con.send(protocol.response_protocol(0, 'Processing...'))
            await asyncio.sleep(30)
    
    # ファイル情報のセット
    def _setFileInfo(self, filename: str) -> None:
        path = 'temp/' + filename
        if os.path.exists(path) == False:
            raise Exception('ファイルが見つかりません。')
        
        self.media_type = os.path.splitext(path)[1]
        self.data_size = os.path.getsize(path)

    # 編集後のファイル名取得
    def _getEditedFileName(self, command: str) -> str:
        # 編集後のファイル名取得
        target = 'temp/'
        filename = command[command.rfind(target) + len(target):]
        print('編集後のファイル名： ' + str(filename))
        return filename

    # ダウンロードデータのファイル名取得とコマンドのファイル名項の書き換え
    def _getFileName(self, json: dict) -> str:
        # ファイル名の取得
        fileName = self._duplicate_rename('recv.mp4')
        json["command"] = json["command"].replace('input', fileName)

        return fileName

    # ファイル名被りを判別してリネームする関数
    def _duplicate_rename(self, file_path: str) -> str:
        if os.path.exists('temp/' + file_path):
            name, ext = os.path.splitext(file_path)
            i = 1
            while True:
                # 被りのあるファイルがあった場合はファイル名の後に（num）を挿入する
                new_name = "{}({}){}".format(name, i, ext)
                if not os.path.exists('temp/' + new_name):
                    return new_name
                i += 1
        else:
            return file_path

    # 指定の動画ファイルを削除
    def _removeSpecifyData(self, filename: str) -> None:
        os.remove('temp/' + filename)




def main():
    tcp = Tcp_server()

    # tcpサーバー起動
    thread1 = threading.Thread(target=tcp.start_thread)
    thread1.start()


if __name__ == '__main__':
    main()