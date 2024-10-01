# FFmpeg-Video-Compressor
動画・音声変換ツール「FFmpeg」を使用した動画圧縮等を行うコンソールアプリケーション  
サーバー：クライアントからダウンロードした動画をffmpegツールにより編集後、クライアントにデータを返す。  
クライアント：任意のmp4ファイルをサーバーにアップロードすると、編集されたデータがサーバーから返ってくる。  

# Requirement
* python3  ver-3.11.4
* ffmpeg   ver-7.0.2 (サーバーのみ)

# Installation
ffmpegのインストール方法
* homeberewでインストールする

```bash
brew install ffmpeg
```
* webサイトからインストールする  
→　https://ffmpeg.org/download.html

# directory
* クライアント
 <pre>
.
└── client
    ├── client.py
    ├── protocol.py
    ├── input　(upload data)
    │   ├── test1.mp4
    │   ├── test2.mp4
    │   └── ...
    ├── output (download data)
        ├── comp_test1.mp4
        ├── comp_test2.mp4
        └── ...
 </pre>
 * サーバー
 <pre>
.
└── server
    ├── server.py
    ├── protocol.py
    ├── temp　(download, upload data)
        ├── test1.mp4
        ├── test2.mp4
        ├── comp_test1.mp4
        ├── comp_test2.mp4
        └── ...   
 </pre>
# Usage
1. サーバー起動
 ```bash
 python3 server.py
 ```
2. クライアントを起動するか、または手動によりinput,outputディレクトリを作成する。  
   ※クライアントを起動すると同じディレクト内にinput,outputディレクトリが作成されます。再度起動する必要あり。
  ```bash
  python3 client.py
  ```
 <pre>
.
└── client
    ├── client.py
    ├── protocol.py
    ├── input　(upload data)
    │   ├── test1.mp4
    │   ├── test2.mp4
    │   └── ...
    ├── output (download data)
        ├── comp_test1.mp4
        ├── comp_test2.mp4
        └── ...
 </pre>


3. inputディレクトリに圧縮操作などを行いたいmp4ファイルを置く
4. コマンド入力により行いたい処理を指定していく
5. ダウンロード完了　（outputディレクトリに保存される）
6. サーバーの停止　　  
Ctr + C  


# Note


 
