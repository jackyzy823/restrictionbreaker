import uuid
from base64 import urlsafe_b64encode
import time

import hmac
import hashlib
import re

import requests
#Cipher




'''
date: Mon, 16 Jul 2018 08:07:56 GMT
applicationKeySecret
:
"2knbNxyXKDNHDy4Tab1nhEUueR5iEub-vt0uSovc5PA"
deviceId
:
"401551ae-086f-45e6-96b3-dfcc176982c7"

'''
# Note: base64 difference
#   NO_PADDING -> remove =
#   URLSAFE -> + and / ->
# Note: UTC time need
# Note Java doFinal -> python 
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

def getVideoKeyFromTicket(ticket):
    deviceId = str(uuid.uuid4())
    res = requests.post("https://api.abema.io/v1/users",json={"deviceId":deviceId,"applicationKeySecret":generateApplicationKeySecret(deviceId)})
    usertoken = res.json()['token'] #for media bearer

    # or pc params -> appVersion=v6.0.2&osLang=ja-JP&osName=pc&osTimezone=Asia%2fTokyo&osVersion=1.0.0' 
    # res = requests.get("https://api.abema.io/v1/media/token" ,params = {"osName":"android","osVersion":"6.0.1","osLang":"ja_JP","osTimezone":"Asia/Tokyo","appId":"tv.abema","appVersion":"3.27.1" } ,headers={"Authorization" :"Bearer "+usertoken})
    res = requests.get("https://api.abema.io/v1/media/token" ,params = {"osName":"pc","osVersion":"1.0.0","osLang":"ja_JP","osTimezone":"Asia/Tokyo","appVersion":"v6.0.2" } ,headers={"Authorization" :"Bearer "+usertoken})

    # print res.status_code
    mediatoken = res.json()['token']

    # m3u8 = requests.get("https://linear-abematv.akamaized.net/channel/abema-anime/1080/playlist.m3u8",headers={"X-Forwarded-For":"1.0.16.0"}).content
    # # print m3u8

    # import re
    # ticket = re.findall(r"abematv-license://(.*)\"",m3u8)[0]

    #this api different in pc and android
    #do cid key req
    res = requests.post("https://license.abema.io/abematv-hls",params={"t":mediatoken},json={"kv":"a","lt":ticket})
    # len(k_pc) = len(k_android)+1 the last bit of k is a number to ...
    # kg -> xhrp.js generation?
    # res = requests.post("https://license.abema.io/abematv-hls",params={"t":mediatoken},json={"kv":"wd" , "kg":376,"lt":ticket})

    # print res.status_code
    # print res.json()

    cid = res.json()['cid']
    key = res.json()['k']


    res = sum([  "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz".find(key[i]) * (58 ** (len(key) -1 - i)) for i in range(len(key)) ])
    import struct
    encdata = struct.pack('>QQ',res >> 64 ,res & 0xffffffffffffffff )
    # print encdata.encode('hex')
    # from RC4 dec(IV:DB98A8E7CECA3424D975280F90BD03EE data:D4B718BBBA9CFB7D0192A58F9E2D146AFC5DB29E4352DE05FC4CF2C1005804BB)
    # Crypto.Cipher.ARC4.new('DB98A8E7CECA3424D975280F90BD03EE'.decode('hex')).decrypt('D4B718BBBA9CFB7D0192A58F9E2D146AFC5DB29E4352DE05FC4CF2C1005804BB'.decode('hex')).encode('hex')
    # res: 3AF0298C219469522A313570E8583005A642E73EDD58E3EA2FB7339D3DF1597E
    h =hmac.new("3AF0298C219469522A313570E8583005A642E73EDD58E3EA2FB7339D3DF1597E".decode("hex"),cid+deviceId ,digestmod=hashlib.sha256)
    enckey = h.digest() #bin mode
    # print enckey.encode('hex')
    from Crypto.Cipher import AES

    aes = AES.new(enckey,AES.MODE_ECB)
    decKey = aes.decrypt(encdata)
    # print decKey.encode("hex")
    return decKey

print getVideoKeyFromTicket("2cxBntsqwKGrFBrCKAta57LGXMreD57Djdh2N7NH7TqF").encode('hex')
for channel in requests.get("https://api.abema.io/v1/channels").json()["channels"]:
    m3u8link = channel["playback"]["hls"].replace("playlist.m3u8",'1080/playlist.m3u8')
    for i in range(10):
        m3u8 = requests.get(m3u8link,headers={"X-Forwarded-For":"1.0.16.0"}).content
        res = re.findall(r"abematv-license://(.*)\"",m3u8)
        if  len(res) != 0:
            ticket = res[0]
            vkey = getVideoKeyFromTicket(ticket)
            print channel["id"].ljust(20,"."),":",ticket,vkey.encode('hex')
            # print channel["id"].ljust(20,"."),": No key"
            break
    else:
        print channel["id"].ljust(20,"."),": No key"

'''
refernece java base64 from  https://android.googlesource.com/platform/frameworks/base/+/master/core/java/android/util/Base64.java
import java.io.UnsupportedEncodingException;
import java.security.InvalidKeyException;
import java.security.Key;
import java.security.NoSuchAlgorithmException;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

//java 8
import java.time.LocalDateTime;
import java.time.ZoneOffset; 
import java.time.temporal.ChronoUnit; 

import javax.xml.bind.DatatypeConverter;


public class Test {
    public static String a(String str, LocalDateTime fVar) {
        Throwable e;
        int i = 0;
        LocalDateTime cQ = fVar.plusHours(1); //+1hour
        try {
            Key secretKeySpec = new SecretKeySpec("v+Gjs=25Aw5erR!J8ZuvRrCx*rGswhB&qdHd_SYerEWdU&a?3DzN9BRbp5KwY4hEmcj5#fykMjJ=AuWz5GSMY-d@H7DMEh3M@9n2G552Us$$k9cD=3TxwWe86!x#Zyhe".getBytes("utf-8"), "HmacSHA256");
            Mac instance = Mac.getInstance("HmacSHA256");
            instance.init(secretKeySpec);
            try {
                int i2;
                instance.update("v+Gjs=25Aw5erR!J8ZuvRrCx*rGswhB&qdHd_SYerEWdU&a?3DzN9BRbp5KwY4hEmcj5#fykMjJ=AuWz5GSMY-d@H7DMEh3M@9n2G552Us$$k9cD=3TxwWe86!x#Zyhe".getBytes("utf-8"));
                byte[] doFinal = instance.doFinal();
                System.out.printf("Step1:%s\n",DatatypeConverter.printHexBinary(doFinal));
                for (i2 = 0; i2 < cQ.getMonthValue(); i2++) {
                    doFinal = instance.doFinal(doFinal);
                    System.out.printf("Dofinal:%s\n",DatatypeConverter.printHexBinary(doFinal));
                }
                System.out.printf("month:%d\n",cQ.getMonthValue());
                try {
                    System.out.printf("Step1:%s\n",DatatypeConverter.printHexBinary(doFinal));
                    byte[] bytes = (Base64.encodeToString(doFinal, 11) + str).getBytes("utf-8");
                    instance.reset();
                    instance.update(bytes);
                    doFinal = instance.doFinal();
                    for (i2 = 0; i2 < cQ.getDayOfMonth() % 5; i2++) {
                        doFinal = instance.doFinal(doFinal);
                    }
                    try {
                        bytes = (Base64.encodeToString(doFinal, 11) + cQ.toEpochSecond(ZoneOffset.UTC)).getBytes("utf-8");
                        instance.reset();
                        instance.update(bytes);
                        bytes = instance.doFinal();
                        while (i < cQ.getHour() % 5) {
                            bytes = instance.doFinal(bytes);
                            i++;
                        }
                        return Base64.encodeToString(bytes, 11);
                    } catch (Throwable e2) {
                        System.out.println("error");
                            return null;
                    }
                } catch (Throwable e22) {
                                            System.out.println("error");

                        return null;
                }
            } catch (Throwable e222) {
                        System.out.println("error");

                    return null;
            }
        } catch (UnsupportedEncodingException e3) {
                        System.out.println("error");

                return null;
        } catch (InvalidKeyException e4) {
                        System.out.println("error");

                return null;
        } catch (NoSuchAlgorithmException e5) {
                        System.out.println("error");

                return null;
        }
    }

    public static void main(String[] args) {
        LocalDateTime dt = LocalDateTime.of(2018, 7, 16, 8, 00); 
        System.out.println(a("uuid",dt));
    }
}

'''

'''For streamlink
from streamlink.plugin import Plugin
from streamlink.plugin.plugin import parse_url_params
from streamlink.utils import update_scheme
from streamlink.stream import HLSStream
from requests.adapters import BaseAdapter
from requests import Response

import hashlib
import hmac
import re
import struct
import time
import uuid
from base64 import urlsafe_b64encode

from Crypto.Cipher import AES


class AbemaTVLicenseAdapter(BaseAdapter):
    def __init__(self,session):
        self._plugin_session = session
        super(AbemaTVLicenseAdapter, self).__init__()

    def _generateApplicationKeySecret(self,deviceId):
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


    def _getVideoKeyFromTicket(self,ticket):
        deviceId = str(uuid.uuid4())
        res = self._plugin_session.http.post("https://api.abema.io/v1/users",json={"deviceId":deviceId,"applicationKeySecret":self._generateApplicationKeySecret(deviceId)})
        usertoken = res.json()['token'] #for media bearer

        # or pc params -> appVersion=v6.0.2&osLang=ja-JP&osName=pc&osTimezone=Asia%2fTokyo&osVersion=1.0.0' 
        res = self._plugin_session.http.get("https://api.abema.io/v1/media/token" ,params = {"osName":"android","osVersion":"6.0.1","osLang":"ja_JP","osTimezone":"Asia/Tokyo","appId":"tv.abema","appVersion":"3.27.1" } ,headers={"Authorization" :"Bearer "+usertoken})
        # print res.status_code
        mediatoken = res.json()['token']

        # m3u8 = requests.get("https://linear-abematv.akamaized.net/channel/abema-anime/1080/playlist.m3u8",headers={"X-Forwarded-For":"1.0.16.0"}).content
        # # print m3u8

        # import re
        # ticket = re.findall(r"abematv-license://(.*)\"",m3u8)[0]

        #do cid key req
        res = self._plugin_session.http.post("https://license.abema.io/abematv-hls",params={"t":mediatoken},json={"kv":"a","lt":ticket})
        # print res.status_code
        # print res.json()

        cid = res.json()['cid']
        key = res.json()['k']


        res = sum([  "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz".find(key[i]) * (58 ** (len(key) -1 - i)) for i in range(len(key)) ])
        encdata = struct.pack('>QQ',res >> 64 ,res & 0xffffffffffffffff )
        # print encdata.encode('hex')
        # from RC4 dec(IV:DB98A8E7CECA3424D975280F90BD03EE data:D4B718BBBA9CFB7D0192A58F9E2D146AFC5DB29E4352DE05FC4CF2C1005804BB)
        # Crypto.Cipher.ARC4.new('DB98A8E7CECA3424D975280F90BD03EE'.decode('hex')).decrypt('D4B718BBBA9CFB7D0192A58F9E2D146AFC5DB29E4352DE05FC4CF2C1005804BB'.decode('hex')).encode('hex')
        # res: 3AF0298C219469522A313570E8583005A642E73EDD58E3EA2FB7339D3DF1597E
        h =hmac.new("3AF0298C219469522A313570E8583005A642E73EDD58E3EA2FB7339D3DF1597E".decode("hex"),cid+deviceId ,digestmod=hashlib.sha256)
        enckey = h.digest() #bin mode
        # print enckey.encode('hex')
        
        aes = AES.new(enckey,AES.MODE_ECB)
        decKey = aes.decrypt(encdata)
        # print decKey.encode("hex")
        return decKey



    def send(self, request, stream=False, timeout=None, verify=True,
             cert=None, proxies=None):
        resp = Response()
        resp.status_code = 200
        resp._content = self._getVideoKeyFromTicket(ticket = re.findall(r"abematv-license://(.*)",request.url)[0])
        return resp

    def close(self):
        pass

    pass

class AbemaTV(Plugin):
    _url_re = re.compile(r"https://abema\.tv/now-on-air/(?P<onair>.+)|https://abema\.tv/video/episode/(?P<episode>.+)|https://abema\.tv/channels/.+?/slots/(?P<slot>.+)")
    #https://abema.tv/video/episode/<id>  -> https://vod-abematv.akamaized.net/program/<id>/playlist.m3u8
    #https://abema.tv/channels/<type>/slots/<id> -> https://vod-abematv.akamaized.net/slot/<id>/playlist.m3u8

    @classmethod
    def can_handle_url(cls, url):
        return cls._url_re.match(url) is not None

    def __init__(self, url):
        super(AbemaTV, self).__init__(url)

    def _get_streams(self):
        url, params = parse_url_params(self.url)
        matchResult = self._url_re.match(url)
        if matchResult.group("onair"):
            channels = self.session.http.get("https://api.abema.io/v1/channels").json()["channels"]
            for i in channels:
                if matchResult.group("onair") == i["id"]:
                    break
            else:
                from streamlink.exceptions import NoStreamsError
                raise NoStreamError 
            playlisturl = i["playback"]["hls"]
        elif matchResult.group("episode"):
            playlisturl = "https://vod-abematv.akamaized.net/program/%s/playlist.m3u8"%(matchResult.group("episode"))
        elif matchResult.group("slot"):
            playlisturl = "https://vod-abematv.akamaized.net/slot/%s/playlist.m3u8"%(matchResult.group("slot"))

        self.logger.debug("Playlist URL={0}; ", playlisturl)
        
        self.session.http.mount("abematv-license://",AbemaTVLicenseAdapter(self.session))

        streams = HLSStream.parse_variant_playlist(self.session, playlisturl)
        if not streams:
            return {"live": HLSStream(self.session, playlisturl)}
        else:
            return streams

__plugin__ = AbemaTV
'''