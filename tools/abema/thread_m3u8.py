from BaseHTTPServer import HTTPServer
from SocketServer import ThreadingMixIn
from SimpleHTTPServer import SimpleHTTPRequestHandler
import requests
import hashlib
import re
import hmac
from Crypto.Cipher import AES,Blowfish,ARC4
import struct
import uuid
import time
import json
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
userid = res.json()['profile']['userId']
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

def to_bigint256_array(key):
    res = sum([  "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz".find(key[i]) * (58 ** (len(key) -1 - i)) for i in range(len(key)) ])
    return struct.pack('>QQQQ',res >> 192, (res>>128 ) & 0xffffffffffffffff ,(res>>64)& 0xffffffffffffffff ,res & 0xffffffffffffffff )


def getMpdKey(post_str,userid,usertoken):
    #mpdxml = requests.get(mpd,headers={"X-Forwarded-For":"1.0.16.0"}).content #thi api has no referer with media token 
    # kid is referer to the program displaying
    # from string uuid -> byte uuid -> b64_url_nopadding uuid
    i#kid =urlsafe_b64encode(uuid.UUID(kidraw).bytes).rstrip('=')
    #print "Kid:",kid

    #TODO appversion from app.js
    # appversion <--relate-> RC4KEY DATAS

    res = session.get("https://api.abema.io/v1/media/token" ,
        params = {"osName":"pc","osVersion":"1.0.0","osLang":"ja_JP","osTimezone":"Asia/Tokyo","appVersion":"v7.0.2" } ,
        headers={"Authorization" :"Bearer "+usertoken})

    mediatoken = res.json()['token']

    #mpd is only supported in pc ,so there's only one kind of license api
    res = requests.post("https://license.abema.io/abematv",params={"t":mediatoken},data = post_str)
    resj = res.json()
    k = res.json()['keys'][0]['k']

    (first,second,third) = k.split('.')
    first_bytes = to_bigint256_array(first)
    second_lastchar = second[-1] #  == "5" or "4" or others
    if second_lastchar == '5':
        second_rest = second[:-1]

        INITHKEY = ARC4.new("".join(map(chr,RC4KEY))).encrypt("".join(map(chr,RC4DATA[4]))) # the 4th data from js
        res1 = hmac.new(INITHKEY,kid+userid,hashlib.sha256).digest() #d
        res2 = hmac.new(res1,userid,hashlib.sha256).digest() #p
        res3 = hmac.new(res1,kid,hashlib.sha256).digest()  #m  # stilllll res1 !!!! 


        KEY2 =  ARC4.new("".join(map(chr,RC4KEY))).encrypt("".join(map(chr,RC4DATA[5]))) # the 5th data from js

        res4 = ARC4.new(KEY2).encrypt(res2) #h
        res5 = ARC4.new(KEY2).encrypt(res3) #b


        second_rest_bytes = to_bigint128_array(second_rest)
        # print map(ord,second_rest_bytes)

        res6 = ARC4.new(res5).encrypt(second_rest_bytes)
        #sth with res6 res4 
        
        res7 = Blowfish.new(res4,Blowfish.MODE_ECB).decrypt(res6)

        IV = third.decode('hex')
        cipertext = res7 

        aes = AES.new(cipertext,AES.MODE_CBC,IV=IV)

        final = aes.decrypt(first_bytes)
        padding = ord(final[-1])
        final = final[:-1*padding]
        resj['keys'][0]['k'] = final 
        return json.dumps(resj)
        #return final
        #return urlsafe_b64decode(final_utf8+"==") #EME use base64(key)
    elif second_lastchar == '4':
        raise NotImplementedError
    else:
        raise NotImplementedError

DASH_PAGE = '''<!DOCTYPE html>
<html>
  <head>
    <!-- Shaka Player compiled library: -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/shaka-player/2.4.3/shaka-player.compiled.debug.js"></script>
    <!-- Your application source: -->
    <script >
var manifestUri =
    '/channel/abema-special/manifest.mpd';

function initApp() {
  // Install built-in polyfills to patch browser incompatibilities.
  shaka.polyfill.installAll();

  // Check to see if the browser supports the basic APIs Shaka needs.
  if (shaka.Player.isBrowserSupported()) {
    // Everything looks good!
    initPlayer();
  } else {
    // This browser does not have the minimum set of APIs we need.
    console.error('Browser not supported!');
  }
}

function initPlayer() {
  // Create a Player instance.
  var video = document.getElementById('video');
  var player = new shaka.Player(video);

  // Attach player to the window to make it easy to access in the JS console.
  window.player = player;

  // Listen for error events.
  player.addEventListener('error', onErrorEvent);

player.configure({
  drm: {
/*   clearKeys: {
        "17aaa6af78f24fe59baa17a65d9885c6":"e906be68a3c64c94ad47f07a1465b48a"
    }
*/

    servers: {
      'org.w3.clearkey':'https://192.168.1.81:8899/clearkey',
    }

  }
});

  // Try to load a manifest.
  // This is an asynchronous process.
  player.load(manifestUri).then(function() {
    // This runs if the asynchronous load is successful.
    console.log('The video has now been loaded!');
  }).catch(onError);  // onError is executed if the asynchronous load fails.
}

function onErrorEvent(event) {
  // Extract the shaka.util.Error object from the event.
  onError(event.detail);
}

function onError(error) {
  // Log the error.
  console.error('Error code', error.code, 'object', error);
}

document.addEventListener('DOMContentLoaded', initApp);

    </script>
  </head>
  <body>
    <video id="video"
           width="640"
           controls autoplay></video>
  </body>
</html>
'''

class M3U8Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if re.match(r"/clearkey",self.path):
            content_len = int(self.headers.getheader('content-length', 0))
            post_body = self.rfile.read(content_len)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(getMpdKey(post_body,userid,usertoken)) 

    def do_GET(self):
        if re.match(r"/$",self.path):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(DASH_PAGE)
 
        if re.match(r"/.*\.mpd",self.path):
            self.send_response(200)
            self.send_header('Content-Type','application/dash+xml')
            self.end_headers()
            res = session.get("https://linear-abematv.akamaized.net"+self.path,headers = {"X-Forwarded-For":japan_ip}).content
            res = res.replace('<BaseURL>https://linear-abematv.akamaized.net/</BaseURL>','<BaseURL>https://192.168.1.81:8899/</BaseURL>')
            self.wfile.write(res)

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
        elif re.match(r"/(?P<ts>.*\.ts)",self.path) :
            # link = re.match(r"/(?P<ts>.*\.ts)").groupdict()["ts"]
            self.send_response(200)
            self.send_header('Content-Type','video/MP2T') # Content-Type: video/mp4
            self.end_headers()
            with session.get("https://linear-abematv.akamaized.net"+self.path,headers = {"X-Forwarded-For":japan_ip},stream = True) as s:
                for  i in s.iter_content(chunk_size=128 * 1024): #chunksize
                    self.wfile.write(i)
            pass
        elif re.match(r"/.*\.m4s",self.path):
            self.send_response(200)
            self.send_header('Content-Type','video/mp4') # Content-Type: video/mp4
            self.end_headers()
            with session.get("https://linear-abematv.akamaized.net"+self.path,headers = {"X-Forwarded-For":japan_ip},stream = True) as s:
                for  i in s.iter_content(chunk_size=128 * 1024): #chunksize
                    self.wfile.write(i)
            

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

server = ThreadedHTTPServer(("0.0.0.0", 8899), M3U8Handler)
#openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes
import ssl
server.socket = ssl.wrap_socket (server.socket, certfile='./server.pem', server_side=True)

server.serve_forever()
# while True:
#     server.handle_request()

