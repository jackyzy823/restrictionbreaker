import argparse
import hashlib
import hmac
import logging
import json
import random
import re
import struct
import sys
import time
import urllib
import uuid

from base64 import urlsafe_b64encode
from binascii import unhexlify

from Crypto.Cipher import AES

from tornado import gen
from tornado.httpclient import AsyncHTTPClient , HTTPClient , HTTPClientError
from tornado.log import enable_pretty_logging
import tornado.ioloop
import tornado.web

enable_pretty_logging()
app_log = logging.getLogger("tornado.application")

parser = argparse.ArgumentParser()
parser.add_argument("-p",help="for those out of japan",action="store_true")
parser.add_argument("-f",help="force resolution in (180,240,360,720,1080,4096)",type=int,choices = (180,240,360,720,1080,4096))
args = parser.parse_args()

#todo quality choose
# use now-on-air
if args.p:
    japan_ip = '1.0.16.24' # todo: generate ip
    app_log.info("Using Japan ip: {0}".format(japan_ip))

if args.f and args.f not in (180,240,360,720,1080,4096):
    app_log.error("Resolution should in {0}".format((180,240,360,720,1080,4096)))
    sys.exit(1)



#TODO: LRU
LICENSE_CACHE={}



channels =  {i["id"]:i["playback"]["hls"].replace("https://linear-abematv.akamaized.net","")   for i in json.loads(HTTPClient().fetch("https://api.abema.io/v1/channels").body)["channels"]}




class ChannelHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self,name):
        if args.f:
            self.redirect("/channel/{0}/{1}/playlist.m3u8".format(name,args.f))
            return
        http_client = AsyncHTTPClient()
        headers = {"X-Forwarded-For":japan_ip} if args.p else {}
        response = yield http_client.fetch("https://linear-abematv.akamaized.net/channel/{0}/playlist.m3u8".format(name), headers = headers)
        # raise gen.Return(response.body)
        self.set_header("Content-Type","application/x-mpegURL")
        self.write(response.body)

class ChannelQualityHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self,name,quality):
        http_client = AsyncHTTPClient()
        headers = {"X-Forwarded-For":japan_ip} if args.p else {}
        response = yield http_client.fetch("https://linear-abematv.akamaized.net/channel/{0}/{1}/playlist.m3u8".format(name,quality), headers = headers)
        res = re.sub("\"(abematv-license)://(\w*)\"",r'"/\1/\2"',response.body)
        if args.p:
            res = re.sub(r"https://linear-abematv\.akamaized\.net",'',res)
        # raise gen.Return(res)
        self.set_header("Content-Type","application/x-mpegURL")
        self.write(res)

class LicenseHandler(tornado.web.RequestHandler):
    def initialize(self,usertoken,deviceid):
        self.usertoken = usertoken
        self.deviceid = deviceid
        pass
    @gen.coroutine
    def get(self,ticket):
        res = LICENSE_CACHE.get(ticket,False)
        if not res:
            val =  yield self._get_videokey_from_ticket(ticket,self.usertoken,self.deviceid)
            LICENSE_CACHE[ticket] = val
            self.write(val)
        else:
            app_log.info("Ticket hit Cache!")
            self.write(res)

    @gen.coroutine
    def _get_videokey_from_ticket(self,ticket,usertoken,deviceid):
        http_client = AsyncHTTPClient()

        params = {
            "osName": "android",
            "osVersion": "6.0.1",
            "osLang": "ja_JP",
            "osTimezone": "Asia/Tokyo",
            "appId": "tv.abema",
            "appVersion": "3.27.1"
        }
        auth_header = {"Authorization": "Bearer " + usertoken}
        res  = yield http_client.fetch("https://api.abema.io/v1/media/token?"+urllib.urlencode(params),headers=auth_header)

        res = json.loads(res.body)

        mediatoken = res['token']

        res = yield http_client.fetch("https://license.abema.io/abematv-hls?"+urllib.urlencode({"t": mediatoken}),method = "POST",
                                      headers={'Content-Type': 'application/json'} ,body=json.dumps({"kv": "a", "lt": ticket}))
        res = json.loads(res.body)

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
        raise gen.Return(rawvideokey)




class TSHandler(tornado.web.RequestHandler):
    @gen.coroutine
    def get(self,ts):
        http_client = AsyncHTTPClient()
        headers = {"X-Forwarded-For":japan_ip} if args.p else {}
        try:
            response = yield http_client.fetch("https://linear-abematv.akamaized.net/"+ts, headers = headers , streaming_callback=self._handle_chunk)
        except HTTPClientError:
            pass
        # self.write(response.body)
        self.finish()

    def _handle_chunk(self,data):
        self.write(data)
        self.flush()

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.redirect(random.choice(channels.values()))

def make_app():
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
    res = json.loads(HTTPClient().fetch("https://api.abema.io/v1/users", method='POST' ,headers={'Content-Type': 'application/json'} , body=json.dumps(json_data)).body)
    usertoken = res['token']



    return tornado.web.Application([
        (r"/",IndexHandler),
        (r"/now-on-air/([^\/^\.]*)",tornado.web.RedirectHandler,{"url": "/channel/{0}/playlist.m3u8"}),
        (r"/channel/(?P<name>[^\/^\.]*?)/playlist\.m3u8", ChannelHandler), 
        (r"/channel/(?P<name>[^\/^\.]*?)/(?P<quality>\d*?)/playlist\.m3u8",ChannelQualityHandler),
        (r"/abematv-license/(?P<ticket>.*)",LicenseHandler,dict(usertoken = usertoken , deviceid = deviceid)),
        (r"/(?P<ts>.*\.ts)",TSHandler)
    ])

if __name__ == "__main__":
    app = make_app()
    app_log.info("Startup service!")
    app.listen(8888)
    try:
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        sys.exit(0)

#TODO async client streaming callback  https://stackoverflow.com/questions/37266144/how-do-i-handle-streaming-data-in-tornado-asynchronously-while-handling-the-res
