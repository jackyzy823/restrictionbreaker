#
# requirements : bottle requests pycrypto
#
#
# TODO use threadingmixin for BaseHTTPServer ?
#
from gevent import monkey;monkey.patch_all()
from bottle import route, run,request , redirect ,response
import requests
session = requests.Session()
import re

import uuid
import random
import hashlib
import hmac
import struct
import time
from base64 import urlsafe_b64encode
from binascii import unhexlify

from Crypto.Cipher import AES

import logging
logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO)

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-p",help="proxy ts",action="store_true")
parser.add_argument("-f",help="force resolution in (180,240,360,720,1080,4096)",type=int,choices = (180,240,360,720,1080,4096))
parser.add_argument("-b",help="ts buffer size (only if -p )",type=int,default=100*1024)
args = parser.parse_args()

if args.p:
    japan_ip = '1.0.16.24' # todo: generate ip
    logging.info("Using Japan ip: {0}".format(japan_ip))
    logging.info("Using ts buffersize: {0}".format(args.b))

if args.f:
    logging.info("Using resolution : {0}".format(args.f))


LICENSE_CACHE={}

def _generate_applicationkeysecret(deviceid):
    SECRETKEY = "v+Gjs=25Aw5erR!J8ZuvRrCx*rGswhB&qdHd_SYerEWdU&a?3DzN9BRbp5KwY4hEmcj5#fykMjJ=AuWz5GSMY-d@H7DMEh3M@9n2G552Us$$k9cD=3TxwWe86!x#Zyhe"
    deviceid = deviceid.encode("utf-8")  # for python3
    # plus 1 hour and drop minute and secs
    # for python3 : floor division
    ts_1hour = (int(time.time()) + 60 * 60) // 3600 * 3600
    time_struct = time.gmtime(ts_1hour)
    ts_1hour_str = str(ts_1hour).encode("utf-8")

    h = hmac.new(SECRETKEY, digestmod=hashlib.sha256)
    h.update(SECRETKEY)
    tmp = h.digest()
    for i in range(time_struct.tm_mon):
        h = hmac.new(SECRETKEY, digestmod=hashlib.sha256)
        h.update(tmp)
        tmp = h.digest()
    h = hmac.new(SECRETKEY, digestmod=hashlib.sha256)
    h.update(urlsafe_b64encode(tmp).rstrip(b"=") + deviceid)
    tmp = h.digest()
    for i in range(time_struct.tm_mday % 5):
        h = hmac.new(SECRETKEY, digestmod=hashlib.sha256)
        h.update(tmp)
        tmp = h.digest()

    h = hmac.new(SECRETKEY, digestmod=hashlib.sha256)
    h.update(urlsafe_b64encode(tmp).rstrip(b"=") + ts_1hour_str)
    tmp = h.digest()

    for i in range(time_struct.tm_hour % 5):  # utc hour
        h = hmac.new(SECRETKEY, digestmod=hashlib.sha256)
        h.update(tmp)
        tmp = h.digest()

    return urlsafe_b64encode(tmp).rstrip(b"=").decode("utf-8")



deviceid = str(uuid.uuid4())
appkeysecret = _generate_applicationkeysecret(deviceid)
json_data = {"deviceId": deviceid, "applicationKeySecret": appkeysecret}
res = session.post("https://api.abema.io/v1/users", json=json_data).json()
usertoken = res['token']

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

# https://linear-abematv.akamaized.net/channel/abema-news/playlist.m3u8
# -> http://localhost:8080/channel/abema-news/playlist.m3u8
# https://linear-abematv.akamaized.net/channel/abema-news/1080/playlist.m3u8
@route('/channel/<name>/playlist.m3u8')
def channel(name):
    if args.f:
        redirect('/channel/{0}/{1}/playlist.m3u8'.format(name,args.f))
    else:
        response.set_header('Content-Type','application/x-mpegURL')
        with session.get("https://linear-abematv.akamaized.net/channel/{0}/playlist.m3u8".format(name),headers = {"X-Forwarded-For":japan_ip} ,stream = True) as s:
            for  i in s.iter_content(chunk_size=args.b): #chunksize
                yield i

@route('/channel/<name>/<quality:int>/playlist.m3u8')
def cq(name,quality):
    response.set_header('Content-Type','application/x-mpegURL')
    #todo async but whatif modify line? using iter_lines?
    with session.get("https://linear-abematv.akamaized.net/channel/{0}/{1}/playlist.m3u8".format(name,quality),headers = {"X-Forwarded-For":japan_ip},stream = True) as r:
        lines = r.iter_lines()
        for line in lines:
            res = re.sub("\"(abematv-license)://(\w*)\"",r'"/\1/\2"',line)
            if args.p:
                res = re.sub(r"https://linear-abematv\.akamaized\.net",'',res)
            yield res+'\n'
    # content = session.get("https://linear-abematv.akamaized.net/channel/{0}/{1}/playlist.m3u8".format(name,quality),headers = {"X-Forwarded-For":japan_ip}).content
    # res = re.sub("\"(abematv-license)://(\w*)\"",r'"/\1/\2"',content)
    # if args.p:
    #     res = re.sub(r"https://linear-abematv\.akamaized\.net",'',res)
    # return res

@route('/abematv-license/<ticket>')
def key(ticket):
    res = LICENSE_CACHE.get(ticket,False)
    if not res:
        val =  _get_videokey_from_ticket(ticket)
        LICENSE_CACHE[ticket] = val
        return val
    return res
          
      
@route('/<p:path>/<n>.ts')
def ts(p,n):
    response.set_header('Content-Type','video/MP2T')
    with session.get("https://linear-abematv.akamaized.net"+request.path,headers = {"X-Forwarded-For":japan_ip},stream = True) as s:
        for  i in s.iter_content(chunk_size=args.b): #chunksize
            yield i
    # return session.get("https://linear-abematv.akamaized.net"+request.path,headers = {"X-Forwarded-For":japan_ip}).content

@route('/now-on-air/<name>')
def nowonair(name):
    redirect("/channel/{0}/playlist.m3u8".format(name))


channels =  {i["id"]:i["playback"]["hls"].replace("https://linear-abematv.akamaized.net","")   for i in session.get("https://api.abema.io/v1/channels").json()["channels"]}


@route('/')
def index():
    redirect(random.choice(channels.values()))



if __name__ == '__main__':
    logging.info("Start service!")
    # run(host='0.0.0.0', port=8080, debug=True)
    run(host='0.0.0.0', port=8080, debug=True , server = 'gevent')

