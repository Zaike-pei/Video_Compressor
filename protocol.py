import json

def prptocol_header(size):
    header  = size.to_bytes(32, 'big')
    return header

# jsonのバイト数(3byte)、データタイプバイト数(1byte)、ペイロードバイト数の送信(28)　３２バイト
def protocol_media_header(json: str, type: str, payload: int) -> bytes:
    json_size = len(ljust_replace_padding(json, 100))
    type_size = len(type)

    return json_size.to_bytes(3, 'big') + type_size.to_bytes(1, 'big') + payload.to_bytes(28, 'big')

# レスポンスプロトコル 16バイト
#　state: ステータスコード 0:継続 1:正常 2: エラー
def response_protocol(state: int, message: str) -> bytes:
    message = ljust_replace_space(message, message.encode('utf-8'), 15)
    return state.to_bytes(1, 'big') + message.encode('utf-8')

def make_json(content: str, type: str, state: int, message: str, command: str) -> str:
    json_data = {
        "filename": content,
        "content-type": type,
        "state": state,
        "message": message,
        "command": command
    }

    return json.dumps(json_data)


# 文字数が上限(num)に達していない場合空文字を補う
def ljust_replace_space(s: str, byte_str: bytes, num: int) -> str:
    return s.ljust(num, ' ') if len(byte_str) < num else s 


# バイト数が下限(num)に達していない場合nullを補う
def ljust_replace_padding(data: str, min_length: int) -> bytes:
    byte_data = data.encode('utf-8')
    if len(byte_data) < min_length:
        padding_length = min_length - len(byte_data)
        byte_data += b'\x00' * padding_length
    
    return byte_data

# バイトデータのjsonデータから'\x00'(null)を削除する
def remove_padding(data: bytes) -> bytes:
    return data.replace(b'\x00', b'')

# ファイルサイズの確認
def fileSize_Check(size: int) -> bool:
    if size < pow(2, 32):
        return True
    else:
        print('this file is too large. (maximum capacity is 4GB)')
        return False

# レスポンスプロトコル使用時のステート値取得
def get_state(header) -> int:
    return header[0]
# レスポンスプロトコル使用時のメッセージ値取得
def get_message(header) -> str:
    return header[1:].decode('utf-8')

def get_json_size(header) -> int:
    return int.from_bytes(header[0:3], 'big')

def get_media_type_size(header) -> int:
    return int.from_bytes(header[3:4], 'big')

def get_payload_size(header) ->int:
    return int.from_bytes(header[4:32], 'big')

 
