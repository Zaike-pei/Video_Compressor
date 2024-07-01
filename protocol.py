

def prptocol_header(size):
    header  = size.to_bytes(32, 'big')
    return header

def protocol_media_header():
    
    return 

# レスポンスプロトコル
#　state: ステータスコード 1:正常 2: エラー
def response_protocol(state, message):
    message = ljust_replace_space(message, message.encode('utf-8'), 15)
    return state.to_bytes(1, 'big') + message.encode('utf-8')


# 文字数が上限(num)に達していない場合空文字を補い、文字列を返す
def ljust_replace_space(s, byte_str, num):
    return s.ljust(num, ' ') if len(byte_str) < num else s 

# ファイルサイズの確認
def fileSize_Check(size):
    print(size)
    if size < pow(2, 32):
        return True
    else:
        print('this file is too large. (maximum capacity is 4GB)')
        return False


def get_state(header):
    return header[0]

def get_message(header):
    # 空白をなくしてた文字列を返す
    return header[1:].decode('utf-8')

 
