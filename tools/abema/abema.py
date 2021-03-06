import base64
import hashlib
import hmac
import json
import re
import struct
import time
import uuid

import requests
from Crypto.Cipher import ARC4, Blowfish, AES


def _urlsafe_b64decode(_str):
    return base64.urlsafe_b64decode(_str + (4 - len(_str) % 4) * '=')


def _urlsafe_b64encode(_str):
    return base64.urlsafe_b64encode(_str).replace('=', '')



#dependencies: struct
def _to_bigint_array(key):
    _s = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    res = sum([_s.find(key[i]) * (58 ** (len(key) - 1 - i))
               for i in range(len(key))])
    if res > 2**128:
        return struct.pack('>QQQQ',
                           res >> 192,
                           (res >> 128) & 0xffffffffffffffff,
                           (res >> 64) & 0xffffffffffffffff,
                           res & 0xffffffffffffffff)
    else:
        return struct.pack('>QQ', res >> 64, res & 0xffffffffffffffff)



def _to_bigint256_array(key):
    _s = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    res = sum([_s.find(key[i]) * (58 ** (len(key) - 1 - i))
               for i in range(len(key))])
    return struct.pack('>QQQQ',
                       res >> 192,
                       (res >> 128) & 0xffffffffffffffff,
                       (res >> 64) & 0xffffffffffffffff,
                       res & 0xffffffffffffffff)


def _to_bigint128_array(key):
    _s = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    res = sum([_s.find(key[i]) * (58 ** (len(key) - 1 - i))
               for i in range(len(key))])
    return struct.pack('>QQ', res >> 64, res & 0xffffffffffffffff)



class Abema(object):
    """docstring for Abema"""
    def __init__(self, token = None):
        super(Abema, self).__init__()
        if token:
            self.usertoken = token
            token_json = _urlsafe_b64decode( token.split(".")[1] )
            self.userid = token_json["sub"]
            self.deviceid = token_json["dev"]
        else:
            (self.userid,self.deviceid,self.usertoken) = generateUserInfo()
            
    @staticmethod
    def generateApplicationKeySecret(deviceid, _time = None):
        if _time == None:
            ts_1hour = (int(time.time())+ 60*60 ) // 3600*3600  # plus 1 hour and drop minute and secs
        else:
            ts_1hour = (int(_time)+ 60*60 ) // 3600*3600  # plus 1 hour and drop minute and secs

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
        h.update(_urlsafe_b64encode(tmp)+deviceid)
        tmp = h.digest()
        for i in range(time_struct.tm_mday % 5):
            h = hmac.new(secretkey,digestmod=hashlib.sha256)
            h.update(tmp)
            tmp = h.digest()
        #step 3
        h = hmac.new(secretkey,digestmod=hashlib.sha256)
        h.update(_urlsafe_b64encode(tmp)+  str(ts_1hour)) # no .0 
        tmp = h.digest()

        for i in range(time_struct.tm_hour  % 5): # should be utc hour!!!
            h = hmac.new(secretkey,digestmod=hashlib.sha256) 
            h.update(tmp)
            tmp = h.digest()

        return _urlsafe_b64encode(tmp)


    @staticmethod
    def generateUserInfo():
        deviceid = str(uuid.uuid4())
        res = requests.post("https://api.abema.io/v1/users",json={"deviceId":deviceid,"applicationKeySecret":generateApplicationKeySecret(deviceid)})
        usertoken = res.json()['token'] #for media bearer 
        # print usertoken
        userid = res.json()['profile']["userId"]
        return (userid,deviceid,usertoken)

        



# dependencies : time hmac hashlib base64.urlsafe_b64encode 

# Note: base64 difference
#   NO_PADDING -> remove =
#   URLSAFE -> + and / ->
# Note: UTC time need
# Note Java doFinal -> python 
def generateApplicationKeySecret(deviceid, _time=None):
    if _time == None:
        _time = time.time()
    # plus 1 hour and drop minute and secs
    ts_1hour = (int(_time) + 60*60) // 3600*3600

    time_struct = time.gmtime(ts_1hour)
    secretkey = "v+Gjs=25Aw5erR!J8ZuvRrCx*rGswhB&"\
                "qdHd_SYerEWdU&a?3DzN9BRbp5KwY4hE"\
                "mcj5#fykMjJ=AuWz5GSMY-d@H7DMEh3M"\
                "@9n2G552Us$$k9cD=3TxwWe86!x#Zyhe"

    h = hmac.new(secretkey, digestmod=hashlib.sha256)
    h.update(secretkey)
    tmp = h.digest()
    for i in range(time_struct.tm_mon):
        h = hmac.new(secretkey, digestmod=hashlib.sha256)
        h.update(tmp)
        tmp = h.digest()
    # step 2
    h = hmac.new(secretkey, digestmod=hashlib.sha256)
    h.update(_urlsafe_b64encode(tmp)+deviceid)
    tmp = h.digest()
    for i in range(time_struct.tm_mday % 5):
        h = hmac.new(secretkey, digestmod=hashlib.sha256)
        h.update(tmp)
        tmp = h.digest()
    # step 3
    h = hmac.new(secretkey, digestmod=hashlib.sha256)
    h.update(_urlsafe_b64encode(tmp) + str(ts_1hour))  # no .0
    tmp = h.digest()

    for i in range(time_struct.tm_hour % 5):  # should be utc hour!!!
        h = hmac.new(secretkey, digestmod=hashlib.sha256)
        h.update(tmp)
        tmp = h.digest()

    return _urlsafe_b64encode(tmp)




#for pc javascript (mpd && m3u8)
# RC4DATA = [[200, 196, 157, 49, 219, 232, 69, 76, 83, 241, 90, 229, 150, 242, 92, 15, 84, 148, 229, 112, 54, 1, 119, 2, 169, 57, 211, 105, 136, 202, 103, 168], [234, 169, 154, 104, 251, 227, 123, 14, 69, 153, 122, 248, 216, 214, 90, 81, 11, 135, 195, 113, 29, 23, 116, 2, 161, 38, 253, 115, 142, 200, 42, 189], [200, 165, 201, 110, 242, 224, 40, 65, 59, 242, 81, 195, 162, 188, 101, 3, 79, 254, 234, 10, 16, 95, 72, 35, 164, 67, 164, 71, 240, 227, 121, 199], [245, 130, 172, 48, 216, 131, 115, 127, 66, 236, 28, 185, 136, 252, 90, 79, 119, 243, 179, 12, 72, 39, 98, 61, 137, 71, 249, 115, 214, 177, 21, 172], [89, 223, 151, 248, 170, 122, 131, 80, 144, 118, 56, 163, 241, 252, 134, 140, 142, 29, 185, 213, 230, 84, 127, 54, 179, 36, 10, 155, 207, 175, 138, 50], [14, 100, 3, 93, 159, 22, 163, 57, 95, 210, 206, 203, 142, 255, 17, 137, 104]]
# RC4KEY = [44, 128, 188, 10, 35, 20]

#dependencies: requests re base64uuid Crypto.Cipher.ARC4 Crypto.Cipher.AES Crypto.Cipher.Blowfish
# kidraw uuid-format string 
# userid string
# usertoken string
def getMpdKey(kidraw, userid, usertoken):
    RC4DATA = [[200, 196, 157, 49, 219, 232, 69, 76,
                83, 241, 90, 229, 150, 242, 92, 15,
                84, 148, 229, 112, 54, 1, 119, 2, 169,
                57, 211, 105, 136, 202, 103, 168],
               [234, 169, 154, 104, 251, 227, 123, 14,
                69, 153, 122, 248, 216, 214, 90, 81,
                11, 135, 195, 113, 29, 23, 116, 2,
                161, 38, 253, 115, 142, 200, 42, 189],
               [200, 165, 201, 110, 242, 224, 40, 65,
                59, 242, 81, 195, 162, 188, 101, 3,
                79, 254, 234, 10, 16, 95, 72, 35,
                164, 67, 164, 71, 240, 227, 121, 199],
               [245, 130, 172, 48, 216, 131, 115, 127,
                66, 236, 28, 185, 136, 252, 90, 79,
                119, 243, 179, 12, 72, 39, 98, 61,
                137, 71, 249, 115, 214, 177, 21, 172],
               [89, 223, 151, 248, 170, 122, 131, 80,
                144, 118, 56, 163, 241, 252, 134, 140,
                142, 29, 185, 213, 230, 84, 127, 54,
                179, 36, 10, 155, 207, 175, 138, 50],
               [14, 100, 3, 93, 159, 22, 163, 57,
                95, 210, 206, 203, 142, 255, 17, 137, 104]]

    RC4KEY = [44, 128, 188, 10, 35, 20]
    # from string uuid -> byte uuid -> b64_url_nopadding uuid
    kid = _urlsafe_b64encode(uuid.UUID(kidraw).bytes)
    # print "Kid:",kid
    print "kid", uuid.UUID(kidraw).bytes.encode('hex')

    # TODO appversion from app.js
    # appversion <--relate-> RC4KEY DATAS

    res = requests.get("https://api.abema.io/v1/media/token",
                       params={"osName": "pc", "osVersion": "1.0.0",
                               "osLang": "ja_JP", "osTimezone": "Asia/Tokyo",
                               "appVersion": "v7.0.2"},
                       headers={"Authorization": "Bearer "+usertoken})

    mediatoken = res.json()['token']

    # mpd is only supported in pc ,so there's only one kind of license api
    res = requests.post("https://license.abema.io/abematv",
                        params={"t": mediatoken}, 
                        json={"kids": [kid], "type": "temporary"})
    k = res.json()['keys'][0]['k']

    (first, second, third) = k.split('.')
    first_bytes = _to_bigint256_array(first)
    second_lastchar = second[-1]  # == "5" or "4" or others
    if second_lastchar == '5':
        second_rest = second[:-1]

        INITHKEY = ARC4.new("".join(map(chr, RC4KEY))).encrypt(
            "".join(map(chr, RC4DATA[4])))  # the 4th data from js
        res1 = hmac.new(INITHKEY, kid+userid, hashlib.sha256).digest()  # d
        res2 = hmac.new(res1, userid, hashlib.sha256).digest()  # p
        # m  # stilllll res1 !!!!
        res3 = hmac.new(res1, kid, hashlib.sha256).digest()

        KEY2 = ARC4.new("".join(map(chr, RC4KEY))).encrypt(
            "".join(map(chr, RC4DATA[5])))  # the 5th data from js

        res4 = ARC4.new(KEY2).encrypt(res2)  # h
        res5 = ARC4.new(KEY2).encrypt(res3)  # b

        second_rest_bytes = _to_bigint128_array(second_rest)
        # print map(ord,second_rest_bytes)

        res6 = ARC4.new(res5).encrypt(second_rest_bytes)
        # sth with res6 res4

        res7 = Blowfish.new(res4, Blowfish.MODE_ECB).decrypt(res6)

        IV = third.decode('hex')
        cipertext = res7

        aes = AES.new(cipertext, AES.MODE_CBC, IV=IV)

        final = aes.decrypt(first_bytes)
        padding = ord(final[-1])
        final = final[:-1*padding]
        # return final

        # EME use base64(key)
        print "key:", _urlsafe_b64decode(final).encode('hex')
        print '"{0}":"{1}"'.format(uuid.UUID(kidraw).bytes.encode('hex'), _urlsafe_b64decode(final).encode('hex'))

    elif second_lastchar == '4':
        raise NotImplementedError
    else:
        raise NotImplementedError


def getM3u8_pc(ticket,userid,usertoken):
    RC4DATA = [[200, 196, 157, 49, 219, 232, 69, 76, 83, 241, 90, 229, 150, 242, 92, 15, 84, 148, 229, 112, 54, 1, 119, 2, 169, 57, 211, 105, 136, 202, 103, 168], [234, 169, 154, 104, 251, 227, 123, 14, 69, 153, 122, 248, 216, 214, 90, 81, 11, 135, 195, 113, 29, 23, 116, 2, 161, 38, 253, 115, 142, 200, 42, 189], [200, 165, 201, 110, 242, 224, 40, 65, 59, 242, 81, 195, 162, 188, 101, 3, 79, 254, 234, 10, 16, 95, 72, 35, 164, 67, 164, 71, 240, 227, 121, 199], [245, 130, 172, 48, 216, 131, 115, 127, 66, 236, 28, 185, 136, 252, 90, 79, 119, 243, 179, 12, 72, 39, 98, 61, 137, 71, 249, 115, 214, 177, 21, 172], [89, 223, 151, 248, 170, 122, 131, 80, 144, 118, 56, 163, 241, 252, 134, 140, 142, 29, 185, 213, 230, 84, 127, 54, 179, 36, 10, 155, 207, 175, 138, 50], [14, 100, 3, 93, 159, 22, 163, 57, 95, 210, 206, 203, 142, 255, 17, 137, 104]]
    RC4KEY = [44, 128, 188, 10, 35, 20]

    #TODO appversion from app.js
    # appversion <--relate-> RC4KEY DATAS

    #may very large
    appjs = requests.get("https://abema.tv/ddd77f68cb459087c695.app.js").content
    appversion = re.findall("appVersion.*?:\"(.*?)\"",appjs)

    params = {"osName":"pc","osVersion":"1.0.0","osLang":"ja_JP","osTimezone":"Asia/Tokyo","appVersion":appversion } 
    res = requests.get("https://api.abema.io/v1/media/token" ,params = params,headers={"Authorization" :"Bearer "+usertoken})
    mediatoken = res.json()['token']

    xhrp = requests.get("https://abema.tv/xhrp.js").content
    j_str = re.findall(r"\'(\{\\x22.*?\\x22\})\'",xhrp)[0]
    res = json.loads(j_str.replace("\\x22",'"'))
    generation = res["generation"]
    XHRKEY = res["key"]

    res = requests.post("https://license.abema.io/abematv-hls",params={"t":mediatoken},json={"kv":"wd","kg":generation,"lt":ticket})

    cid = res.json()['cid']
    key = res.json()['k']


    print cid,
    # print key
    key_lastchar = key[-1]
    key_res = key[:-1]

    if key_lastchar == '5':
        INITHKEY = ARC4.new("".join(map(chr,RC4KEY))).encrypt("".join(map(chr,RC4DATA[4])))
        XHRKEY2 =hmac.new(INITHKEY,XHRKEY,hashlib.sha256).digest() 
       
        res1 = hmac.new(XHRKEY2,cid+userid,hashlib.sha256).digest() 
        res2 = hmac.new(res1,userid,hashlib.sha256).digest() 
        res3 = hmac.new(res1,cid,hashlib.sha256).digest()

        KEY2 = ARC4.new("".join(map(chr,RC4KEY))).encrypt("".join(map(chr,RC4DATA[5]))) # the 5th data from js
        res4 = ARC4.new(KEY2).encrypt(res2)
        res5 = ARC4.new(KEY2).encrypt(res3)

        key_res_bytes = _to_bigint128_array(key_res)
        res6 = ARC4.new(res5).encrypt(key_res_bytes)
        res7 = Blowfish.new(res4,Blowfish.MODE_ECB).decrypt(res6)
        return res7
    elif key_lastchar == '4':
        raise NotImplementedError
    else:
        raise NotImplementedError

    pass


def getM3u8Key_android(ticket,deviceid,usertoken):
    params = {"osName":"android","osVersion":"6.0.1","osLang":"ja_JP","osTimezone":"Asia/Tokyo","appId":"tv.abema",
                "appVersion":"3.27.1" }  # TODO appVersion <----relates with ---> RC4KEY
    res = requests.get("https://api.abema.io/v1/media/token" ,params = params,headers={"Authorization" :"Bearer "+usertoken})
    # res = requests.get("https://api.abema.io/v1/media/token" ,params = {"osName":"pc","osVersion":"1.0.0","osLang":"ja_JP","osTimezone":"Asia/Tokyo","appVersion":"v6.0.2" } ,headers={"Authorization" :"Bearer "+usertoken})

    mediatoken = res.json()['token']

    #this api different in pc and android
    #do cid key req
    res = requests.post("https://license.abema.io/abematv-hls",params={"t":mediatoken},json={"kv":"a","lt":ticket})
    # len(k_pc) = len(k_android)+1 the last bit of k is a number to ...
    # kg -> xhrp.js generation?
    # res = requests.post("https://license.abema.io/abematv-hls",params={"t":mediatoken},json={"kv":"wd" , "kg":376,"lt":ticket})


    cid = res.json()['cid']
    key = res.json()['k']
    # print cid,
    # print key
    encdata = _to_bigint128_array(key)

    # print encdata.encode('hex')
    # from RC4 dec(IV:DB98A8E7CECA3424D975280F90BD03EE data:D4B718BBBA9CFB7D0192A58F9E2D146AFC5DB29E4352DE05FC4CF2C1005804BB)
    # Crypto.Cipher.ARC4.new('DB98A8E7CECA3424D975280F90BD03EE'.decode('hex')).decrypt('D4B718BBBA9CFB7D0192A58F9E2D146AFC5DB29E4352DE05FC4CF2C1005804BB'.decode('hex')).encode('hex')
    # res: 3AF0298C219469522A313570E8583005A642E73EDD58E3EA2FB7339D3DF1597E
    h =hmac.new("3AF0298C219469522A313570E8583005A642E73EDD58E3EA2FB7339D3DF1597E".decode("hex"),cid+deviceid ,digestmod=hashlib.sha256)
    enckey = h.digest() #bin mode
    # print enckey.encode('hex')
    from Crypto.Cipher import AES

    aes = AES.new(enckey,AES.MODE_ECB)
    decKey = aes.decrypt(encdata)
    # print decKey.encode("hex")
    return decKey

'''
Not works 90-1072_s0_ ?dt=android&enc=pr -> X-ENC-PLAYREADY
                        without --> sample video tsda
                        has dash ???
90-509_s0_ 
90-490_s0_p24
'''
def getM3u8Key(link,deviceid,userid,usertoken):
    m3u8 = requests.get(link,headers={"X-Forwarded-For":"1.0.16.0"}).content
    res = re.findall(r"abematv-license://(.*)\"",m3u8)
    if not res: #may not exists
        return None
    ticket = res[0]

    key1 = getM3u8Key_android(ticket,deviceid,usertoken).encode('hex')
    # key2 =  getM3u8_pc(ticket,userid,usertoken).encode('hex')
    # assert(key1==key2)
    # print key2
    return key1
    # return getM3u8_pc(ticket,userid,usertoken)


def generateUserInfo():
    deviceid = str(uuid.uuid4())
    res = requests.post("https://api.abema.io/v1/users",json={"deviceId":deviceid,"applicationKeySecret":generateApplicationKeySecret(deviceid)})
    usertoken = res.json()['token'] #for media bearer 
    # print usertoken
    userid = res.json()['profile']["userId"]
    return (userid,deviceid,usertoken)

def refreshUserInfo(userid,usertoken):
    resp = requests.get("https://api.abema.io/v1/users/{0}".format(userid), headers={"Authorization" :"Bearer "+usertoken})
    return resp.status_code == 200


def processUrl(link):
    (userid,deviceid,usertoken) = generateUserInfo()
    if link.endswith(".mpd"):
        mpdxml = requests.get(link,headers={"X-Forwarded-For":"1.0.16.0"}).content #thi api has no referer with media token 
        # kid is referer to the program displaying
        kidraw = re.findall(r'''cenc:default_KID=\"(.+?)\"''',mpdxml)[0] # kidraw in format xxxx-xxxx-xxxx-xxx like uuid
        getMpdKey(kidraw,userid,usertoken) # usertoken contains userid
    elif link.endswith(".m3u8"):
        getM3u8Key(link,deviceid,userid,usertoken)


if __name__ == '__main__':
    # test : generateApplicationKeySecret
    assert( 'JHdWjCPqtT4Eqc-NNUhGzO-ndGSBLojb0JNs_nJ85PI' == generateApplicationKeySecret('a8167a4f-71c6-492d-830f-e72a1d5baa11',1534728857.036203))
    
    # test: _to_bigint_array
    assert( 'N\x03]*\x03S\x84~\xdcs\xc1\x17VrV\x8e' == _to_bigint128_array("Adjkljflvrv3kf4asasdad") )
    assert( '\x8f"kQ\x1f\xc2\xb2\xdd\xc62!\x13x\xc3\xccNe\xd4\xcc\xf1s.\x7f\x9a\xf3\xa9\xe5wm\xf2V\x8e' == _to_bigint256_array("Adjkljflvrv3kf4asasdadAdjkljflvrv3kf4asasdad"))
    assert( 'N\x03]*\x03S\x84~\xdcs\xc1\x17VrV\x8e' == _to_bigint_array("Adjkljflvrv3kf4asasdad") )
    assert( '\x8f"kQ\x1f\xc2\xb2\xdd\xc62!\x13x\xc3\xccNe\xd4\xcc\xf1s.\x7f\x9a\xf3\xa9\xe5wm\xf2V\x8e' == _to_bigint_array("Adjkljflvrv3kf4asasdadAdjkljflvrv3kf4asasdad"))

# processUrl("https://linear-abematv.akamaized.net/channel/abema-special/manifest.mpd")
# processUrl("https://linear-abematv.akamaized.net/channel/abema-news/1080/playlist.m3u8")


# for channel in requests.get("https://api.abema.io/v1/channels").json()["channels"]:
#     m3u8link = channel["playback"]["hls"].replace("playlist.m3u8",'1080/playlist.m3u8')
#     print channel["id"],":",
#     processUrl(m3u8link)
#         # m3u8 = requests.get(m3u8link,headers={"X-Forwarded-For":"1.0.16.0"}).content
#         # res = re.findall(r"abematv-license://(.*)\"",m3u8)
#         # if  len(res) != 0:
#         #     ticket = res[0]
#         #     vkey = getVideoKeyFromTicket(ticket)
#         #     print channel["id"].ljust(20,"."),":",ticket,vkey.encode('hex')
#         #     # print channel["id"].ljust(20,"."),": No key"
#         #     break
#         # print channel["id"].ljust(20,"."),": No key"
#     print 
#     if channel["playback"].get("dash",False):
#         processUrl(channel["playback"]["dash"])
