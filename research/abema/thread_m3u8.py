from BaseHTTPServer import HTTPServer
from SocketServer import ThreadingMixIn
from SimpleHTTPServer import SimpleHTTPRequestHandler
import requests
import hashlib
import re
import hmac
from Crypto.Cipher import AES
import struct
import uuid
import time
from base64 import urlsafe_b64encode,urlsafe_b64decode

session = requests.Session()
japan_ip = '1.0.16.24'

def generateApplicationKeySecret(deviceId):
    ts_1hour = (int(time.time())+ 60*60 ) /3600*3600  # plus 1 hour and drop minute and secs
    time_struct = time.gmtime(ts_1hour)   

    secretkey = "v+Gjs=25Aw5erR!J8ZuvRrCx*rGswhB&qdHd_SYerEWdU&a?3DzN9BRbp5KwY4hEmcj5#fykMjJ=AuWz5GSMY-d@H7DMEh3M@9n2G552Us$$k9cD=3TxwWe86!x#Zyhe"

    h = hmac.new(secretkey,digestmod=hashlib.sha256)
    h.update(secretkey)
    tmp = h.digest()
    for i in range(time_struct.tm_mon):
        h = hmac.new(secretkey,digestmod=hashlib.sha256)
        h.update(tmp)
        tmp = h.digest()
    # step 2
    h = hmac.new(secretkey,digestmod=hashlib.sha256)
    h.update(urlsafe_b64encode(tmp).rstrip("=")+deviceId)
    tmp = h.digest()
    for i in range(time_struct.tm_mday % 5):
        h = hmac.new(secretkey,digestmod=hashlib.sha256)
        h.update(tmp)
        tmp = h.digest()
    #step 3
    h = hmac.new(secretkey,digestmod=hashlib.sha256)
    h.update(urlsafe_b64encode(tmp).rstrip("=")+  str(ts_1hour)) # no .0 
    tmp = h.digest()

    for i in range(time_struct.tm_hour  % 5): # should be utc hour!!!
        h = hmac.new(secretkey,digestmod=hashlib.sha256) 
        h.update(tmp)
        tmp = h.digest()

    return urlsafe_b64encode(tmp).rstrip("=")

def to_bigint128_array(key):
    res = sum([  "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz".find(key[i]) * (58 ** (len(key) -1 - i)) for i in range(len(key)) ])
    return struct.pack('>QQ',res >> 64 ,res & 0xffffffffffffffff )


deviceid = str(uuid.uuid4())
res = requests.post("https://api.abema.io/v1/users",json={"deviceId":deviceid,"applicationKeySecret":generateApplicationKeySecret(deviceid)})
usertoken = res.json()['token'] #for media bearer 
print "Init with device",deviceid
print "Init with token",usertoken

LICENSE_CACHE={}

def _get_videokey_from_ticket(ticket):
    params = {
        "osName": "android",
        "osVersion": "6.0.1",
        "osLang": "ja_JP",
        "osTimezone": "Asia/Tokyo",
        "appId": "tv.abema",
        "appVersion": "3.27.1"
    }
    auth_header = {"Authorization": "Bearer " + usertoken}
    res = session.get("https://api.abema.io/v1/media/token", params=params,
                                 headers=auth_header).json()

    mediatoken = res['token']

    res = session.post("https://license.abema.io/abematv-hls",
                                  params={"t": mediatoken},
                                  json={"kv": "a", "lt": ticket}).json()

    cid = res['cid']
    k = res['k']

    res = sum(["123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz".find(k[i]) * (58 ** (len(k) - 1 - i))
              for i in range(len(k))])
    encvideokey = struct.pack('>QQ', res >> 64, res & 0xffffffffffffffff)

    # HKEY:
    # RC4KEY = unhexlify('DB98A8E7CECA3424D975280F90BD03EE')
    # RC4DATA = unhexlify(b'D4B718BBBA9CFB7D0192A58F9E2D146A'
    #                     b'FC5DB29E4352DE05FC4CF2C1005804BB')
    # rc4 = ARC4.new(RC4KEY)
    # HKEY = rc4.decrypt(RC4DATA)
    h = hmac.new("3AF0298C219469522A313570E8583005A642E73EDD58E3EA2FB7339D3DF1597E".decode("hex"),
                 (cid + deviceid).encode("utf-8"),
                 digestmod=hashlib.sha256)
    enckey = h.digest()

    aes = AES.new(enckey, AES.MODE_ECB)
    rawvideokey = aes.decrypt(encvideokey)

    return rawvideokey



class M3U8Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if re.match(r"/now-on-air/(?P<name>[^\/^\.]*)",self.path):
            name = re.match(r"/now-on-air/(?P<name>[^\/^\.]*)",self.path).groupdict()["name"]
            self.send_response(302)
            self.send_header("Location","/channel/{0}/playlist.m3u8".format(name))
            self.end_headers()
            return  
        elif re.match(r"/channel/(?P<name>[^\/^\.]*?)/playlist\.m3u8",self.path):
            name  = re.match(r"/channel/(?P<name>[^\/^\.]*?)/playlist\.m3u8",self.path).groupdict()["name"]
            self.send_response(200)
            self.send_header('Content-Type','application/x-mpegURL')
            self.end_headers()
            self.wfile.write(session.get("https://linear-abematv.akamaized.net/channel/{0}/playlist.m3u8".format(name),headers = {"X-Forwarded-For":japan_ip}).content)
            return
            pass
        elif re.match(r"/channel/(?P<name>[^\/^\.]*?)/(?P<quality>\d*?)/playlist\.m3u8",self.path):
            res = re.match(r"/channel/(?P<name>[^\/^\.]*?)/(?P<quality>\d*?)/playlist\.m3u8",self.path).groupdict()
            name = res["name"]
            quality = res["quality"]
            res = session.get("https://linear-abematv.akamaized.net/channel/{0}/{1}/playlist.m3u8".format(name,quality),headers = {"X-Forwarded-For":japan_ip}).content
            res = re.sub("\"(abematv-license)://(\w*)\"",r'"/\1/\2"',res)
            res = re.sub(r"https://linear-abematv\.akamaized\.net",'',res)
            self.send_response(200)
            self.send_header('Content-Type','application/x-mpegURL')
            self.end_headers()
            self.wfile.write(res)
            pass
        elif re.match(r"/abematv-license/(?P<ticket>.*)",self.path):
            ticket = re.match(r"/abematv-license/(?P<ticket>.*)",self.path).groupdict()["ticket"]
            res = LICENSE_CACHE.get(ticket,False)
            if not res:
                res =  _get_videokey_from_ticket(ticket)
                LICENSE_CACHE[ticket] = res
            self.send_response(200)
            self.end_headers()
            self.wfile.write(res)
            pass
        elif re.match(r"/(?P<ts>.*\.ts)",self.path):
            # link = re.match(r"/(?P<ts>.*\.ts)").groupdict()["ts"]
            self.send_response(200)
            self.send_header('Content-Type','video/MP2T')
            self.end_headers()
            with session.get("https://linear-abematv.akamaized.net"+self.path,headers = {"X-Forwarded-For":japan_ip},stream = True) as s:
                for  i in s.iter_content(chunk_size=128 * 1024): #chunksize
                    self.wfile.write(i)
            pass


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

server = ThreadedHTTPServer(("0.0.0.0", 8899), M3U8Handler)
server.serve_forever()
# while True:
#     server.handle_request()
