import base64
import requests
import time
from datetime import datetime
import re
import subprocess
import threading
import os

if os.path.exists("combine.aac"):
    os.remove("combine.aac")
    print("rm combine.aac")
directry = "D:\\radiko"
for filename in os.listdir(directry):
    if filename.endswith(".ts"):
        file_path = os.path.join(directry, filename)
        os.remove(file_path)
        print("rm .ts")

RADIKO_KEY = b'bcd151073c03b352e1ef2fd66c32209da9ca0afa'

auth1_url = "https://radiko.jp/v2/api/auth1"
auth1_headers = {
    'X-Radiko-App': 'pc_html5',
    'X-Radiko-App-Version': '0.0.1',
    'X-Radiko-Device': 'pc',
    'X-Radiko-User': 'dummy_user',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
}

auth1_response = requests.get(auth1_url, headers=auth1_headers)

authtoken = auth1_response.headers['X-Radiko-AUTHTOKEN']
keyoffset = int(auth1_response.headers['X-Radiko-KEYOFFSET'])
keylength = int(auth1_response.headers['X-Radiko-KEYLENGTH'])

partial_key = base64.b64encode(RADIKO_KEY[keyoffset:keyoffset + keylength]).decode('utf-8')

auth2_url = "https://radiko.jp/v2/api/auth2"
auth2_headers = {
    'X-Radiko-AuthToken': authtoken,
    'X-Radiko-PartialKey': partial_key,
    'X-Radiko-User': 'dummy_user',
    'X-Radiko-Device': 'pc',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
}

auth2_response = requests.get(auth2_url, headers=auth2_headers)

if auth2_response.status_code == 200:
    print("認証成功")
    print("レスポンス:", auth2_response.text)
else:
    print("認証失敗")
    print("ステータスコード:", auth2_response.status_code)

output_aac = "combine.aac"
def ffplay(output_aac):
    subprocess.run(['ffplay', output_aac])
ffmpeg_thread = threading.Thread(target=ffplay, args=(output_aac,))
ffmpeg_thread.daemon = True
ffmpeg_thread.start()
base_url = "https://tf-f-rpaa-radiko.smartstream.ne.jp/tf/playlist.m3u8"
while True:
        start_time = time.localtime()
        formatted_start_time = int(time.strftime('%Y%m%d%H', start_time))
        ft = formatted_start_time
        end_time = formatted_start_time + 1
        to = formatted_start_time + 1
        current_time = datetime.now()
        seek = int(current_time.strftime('%Y%m%d%H%M%S'))
        seek -= 300
        url = f"{base_url}?station_id=802&start_at={str(formatted_start_time)+'0000'}&ft={str(ft)+'0000'}&end_at={str(end_time)+'0000'}&to={str(to)+'0000'}&seek={seek}&preroll=0&l=15&lsid=eb1c02025639072f88f0cbe7a217eba1&type=b"
        response_m3u8 = requests.get(url,headers=auth2_headers)
        if response_m3u8.status_code == 200:
            url_list = re.findall(r'https?://[^\s]+', response_m3u8.text)
            for segment_url in url_list:
                response_audio = requests.get(segment_url, headers=auth2_headers)
                if response_audio.status_code == 200:
                    timestamp = int(time.time())
                    output_file = f"radiko_audio_{timestamp}.ts"
                    with open(output_file, 'ab') as f:
                        f.write(response_audio.content)
                    print(f"ダウンロード成功: {output_file}")
                    ts_file_path = f'radiko_audio_{timestamp}.ts'
                    with open(ts_file_path, mode="r") as f:
                        file_content = f.read()
                        aac_url_list = re.findall(r'https?://[^\s]+', file_content)
                    for url in aac_url_list:
                        with open(output_aac, mode="ab") as f:
                            response = requests.get(url)
                            f.write(response.content)
                    time.sleep(13.8)
                    os.remove(f'radiko_audio_{timestamp}.ts')
            else:
                print(f"音声ダウンロード失敗: {response_audio.status_code}")
        else:
            print("m3u8の取得に失敗しました")