import socket
import time
import datetime
import os
import json
import protocol
import asyncio
from multiprocessing import Process 
from multiprocessing import Lock
import uuid


class Tcp_server:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = '0.0.0.0'
        self.server_port = 9001
        self.header_buffer_size = 32
        self.response_buffer_size = 16
        self.stream_rate = 1400
        self.file_lock = Lock()
        
    # サーバー起動
    def start_server(self):
        # ダウンロードした動画、編集済みデータを保存するディレクトリの作成
        if not os.path.exists('temp'):
            os.makedirs('temp')

        self.sock.bind((self.server_address, self.server_port))
        print('[TCP]Starting up on {} port {}'.format(self.server_address,self.server_port))
        self.sock.listen(5)
        print('[TCP]Waiting for connection...')
        # 接続あればプロセスを作成して各クライアントとの接続を開始
        while True:
            connection, address = self.sock.accept()
            print('[TCP]connecting from {} {}'.format(address, self._time_stamp()))

            process = Process(target=self._handle_client_process, args=(connection, address))
            process.start()
            connection.close()
    
    # コルーチン起動
    def _handle_client_process(self, con, address):
        asyncio.run(self._handle_client(con, address))

    # クライアントとのデータの送受信を開始
    async def _handle_client(self, con, address):
        try:
            while True:
                #ヘッダデータを受信
                header = con.recv(self.header_buffer_size)
                # ヘッダデータ取得失敗
                if header == b'':
                    con.send(protocol.response_protocol(2, 'error'))
                    raise Exception('ヘッダー受信シーケンスでエラーが発生しました。')
                
                # ヘッダ取得完了のレスポンスを返す
                con.send(protocol.response_protocol(1, 'recieved header'))

                # データを受信
                resultsList = self._recievData(con, protocol.get_json_size(header), protocol.get_media_type_size(header), protocol.get_payload_size(header))
                # データ取得失敗
                if resultsList["state"] != 1:
                    con.send(protocol.response_protocol(2, 'failed upload'))
                    raise Exception('データ受信シーケンスでエラーが発生しました。')
                
                # データ取得完了のレスポンスを送信
                con.send(protocol.response_protocol(1, 'recieved data'))

                # 動画編集とクライアントへのメッセージ送信をタスクで実行
                tasks = [asyncio.create_task(self._video_Editing(resultsList["json_data"]['command'])),
                            asyncio.create_task(self._send_message_loop(con))]
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

                for task in done:
                    # 動画編集処理が失敗
                    if task.result() != 0:
                        con.send(protocol.response_protocol(2, 'error'))
                        raise Exception('動画編集シーケンスでエラーが発生しました。')
                    # 編集完了のレスポンスを送信
                    con.send(protocol.response_protocol(1, 'done'))

                for task in tasks:
                    task.cancel()

                # ダウンロードデータを削除
                self._removeData(resultsList["file_name"])
                # 編集後のファイル情報を取得
                fileInfoList = self._setFileInfo(self._getEditedFileName(resultsList["json_data"]["command"]))
                # jsonの作成
                json_data = protocol.make_json(fileInfoList["file_name"], fileInfoList["media_type"], 1, '', '')
                # ヘッダの作成
                header = protocol.protocol_media_header(json_data, fileInfoList["media_type"], fileInfoList["data_size"])
                #　ヘッダーの送信
                con.send(header)
                # クライアントの応答受信
                response = con.recv(self.response_buffer_size)

                # ヘッダー送信失敗
                if protocol.get_state(response) != 1:
                    raise Exception('ヘッダー送信シーケンスでエラーが発生しました。')
                
                # 編集後のデータを送信
                self._uploadData(con, fileInfoList["file_name"], json_data, fileInfoList["media_type"])
                # クライアントがデータを受信できたかの確認をするレスポンスを受け取る
                response = con.recv(self.response_buffer_size)

                # クライアント側でダウンロードエラー
                if protocol.get_state(response) != 1:
                    print('クライアントがデータ受信段階においてエラーが発生しています。')
                    raise Exception('クライアント側で受信エラーが発生しました。接続を閉じます。')
                
                # 編集後のデータを削除する
                self._removeData(fileInfoList["file_name"])

                print('[TCP]disconnect from {} {}'.format(address, self._time_stamp()))
                break

        except Exception as err:
            print(f'[TCP]Error: {str(err)}')
        finally:
            print('[TCP]closing socket')
            con.close()

    # データ受信処理
    def _recievData(self, con: socket, json_size: int, media_type_size: int, data_size: int) -> dict:
        state = -1
        # jsonデータの受信
        json_data = protocol.remove_padding(con.recv(json_size))
        json_data = json.loads(json_data.decode('utf-8'))
        # ファイル名の取得とコマンドのファイル名項の書き換え
        fileName = self._generateFileName(json_data)
        # メディアタイプデータの受信
        media_type = con.recv(media_type_size)
        # 動画データをダウンロード
        flag = True
        with self.file_lock:
            with open('temp/' + fileName, 'wb+') as f:
                while data_size > 0:
                    data = con.recv(data_size if data_size <= self.stream_rate else self.stream_rate)
                    f.write(data)
                    data_size -= len(data)
                    # 受信するべきデータがまだ残っている且つ受信データが無い場合処理中断
                    if len(data) == 0 and data_size > 0:
                        print('接続の問題によりクライアントからの受信データがないため受信待ちを終了します。')
                        flag = False
                        break
        # ダウンロード結果をフラッグで判定
        if flag:
            state = 1
        else:
            print('動画ダウンロード中にエラーが発生しました。')
            state = 0
        
        return {"json_data":json_data, "file_name":fileName, "media_type":media_type, "state":state}
            
    # データ送信
    def _uploadData(self, con: socket, filename: str, json: str, media_type) -> None:
        # jsonデータの送信
        con.send(protocol.ljust_replace_padding(json ,100))
        # メディアタイプの送信
        con.send(media_type.encode('utf-8'))
        # 動画データの送信
        #with self.file_lock:
        with open('temp/' + filename, 'rb') as f:
            data = f.read(self.stream_rate)
            while data:
                con.send(data)
                data = f.read(self.stream_rate)

    # 動画ファイル編集（ffmpeg）
    async def _video_Editing(self, command:str) -> int:
        # サブプロセス実行
        proc = await asyncio.create_subprocess_exec(
            *command.split(' '),
            stdout = asyncio.subprocess.PIPE,
            stderr= asyncio.subprocess.PIPE
        )
        # バッファリング防止
        await proc.communicate()
        # サブプロセスの終了コードを取得
        returncode = await proc.wait()

        return returncode
  
    # 処理待機用関数
    async def _send_message_loop(self, con: socket) -> None:
        while True:
            con.send(protocol.response_protocol(0, 'Processing...'))
            await asyncio.sleep(30)
    
    # ファイル情報のセット
    def _setFileInfo(self, filename: str) -> dict:
        try:
            path = 'temp/' + filename
            if os.path.exists(path) == False:
                raise Exception('ファイルが見つかりません。')
            
            media_type = os.path.splitext(path)[1]
            data_size = os.path.getsize(path)

            return {"file_name": filename, "media_type": media_type, "data_size": data_size}
        except OSError as err:
            print(f"Error: {err.strerror}")

    # 編集後のファイル名取得
    def _getEditedFileName(self, command: str) -> str:
        target = 'temp/'
        filename = command[command.rfind(target) + len(target):]
        return filename

    # ファイル名生成とコマンドのファイル名項の書き換え
    def _generateFileName(self, json: dict) -> str:
        # ファイル名の取得
        timestamp = time.time()
        unique_id = uuid.uuid4()
        fileName = f'recv_{timestamp}_{unique_id}'
        # コマンドの書き換え
        json["command"] = json["command"].replace('input', fileName)
        json["command"] = json["command"].replace('output', fileName)

        return fileName + '.mp4'

    # 指定の動画ファイルを削除
    def _removeData(self, filename: str) -> None:
        try:
            if os.path.exists('temp/' + filename): 
                # ファイル操作競合回避のためロック
                with self.file_lock:
                    os.remove('temp/' + filename)
        except OSError as err:
            print(f"Error: {err.strerror}")

    # タイムスタンプ
    def _time_stamp(self) -> str:
        t_delta = datetime.timedelta(hours=9)
        jst = datetime.timezone(t_delta, 'JST')
        now = datetime.datetime.now(jst)
        return now.strftime('%Y/%m/%d %H:%M:%S')

def main():
    tcp = Tcp_server()
    # tcpサーバー起動
    tcp.start_server()


if __name__ == '__main__':
    main()