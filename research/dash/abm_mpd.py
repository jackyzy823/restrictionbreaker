from lxml import etree as et
import requests
import time

import hashlib
import hmac
import json
import re
import struct
import uuid
from base64 import urlsafe_b64encode,urlsafe_b64decode
from Crypto.Cipher import ARC4 ,Blowfish ,AES



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


def generateUserInfo():
    deviceId = str(uuid.uuid4())
    res = requests.post("https://api.abema.io/v1/users",json={"deviceId":deviceId,"applicationKeySecret":generateApplicationKeySecret(deviceId)})
    usertoken = res.json()['token'] #for media bearer 
    # print usertoken
    userid = res.json()['profile']["userId"]
    return (userid,deviceId,usertoken)

(userid,deviceid,usertoken) = generateUserInfo()

#dependencied: struct
def to_bigint_array(key):
    res = sum([  "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz".find(key[i]) * (58 ** (len(key) -1 - i)) for i in range(len(key)) ])
    if res > 2*128:
        return struct.pack('>QQQQ',res >> 192, (res>>128 ) & 0xffffffffffffffff ,(res>>64)& 0xffffffffffffffff ,res & 0xffffffffffffffff )
    else:
        return struct.pack('>QQ',res >> 64 ,res & 0xffffffffffffffff )

def to_bigint256_array(key):
    res = sum([  "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz".find(key[i]) * (58 ** (len(key) -1 - i)) for i in range(len(key)) ])
    return struct.pack('>QQQQ',res >> 192, (res>>128 ) & 0xffffffffffffffff ,(res>>64)& 0xffffffffffffffff ,res & 0xffffffffffffffff )

def to_bigint128_array(key):
    res = sum([  "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz".find(key[i]) * (58 ** (len(key) -1 - i)) for i in range(len(key)) ])
    return struct.pack('>QQ',res >> 64 ,res & 0xffffffffffffffff )

#for pc javascript (mpd && m3u8)
RC4DATA = [[200, 196, 157, 49, 219, 232, 69, 76, 83, 241, 90, 229, 150, 242, 92, 15, 84, 148, 229, 112, 54, 1, 119, 2, 169, 57, 211, 105, 136, 202, 103, 168], [234, 169, 154, 104, 251, 227, 123, 14, 69, 153, 122, 248, 216, 214, 90, 81, 11, 135, 195, 113, 29, 23, 116, 2, 161, 38, 253, 115, 142, 200, 42, 189], [200, 165, 201, 110, 242, 224, 40, 65, 59, 242, 81, 195, 162, 188, 101, 3, 79, 254, 234, 10, 16, 95, 72, 35, 164, 67, 164, 71, 240, 227, 121, 199], [245, 130, 172, 48, 216, 131, 115, 127, 66, 236, 28, 185, 136, 252, 90, 79, 119, 243, 179, 12, 72, 39, 98, 61, 137, 71, 249, 115, 214, 177, 21, 172], [89, 223, 151, 248, 170, 122, 131, 80, 144, 118, 56, 163, 241, 252, 134, 140, 142, 29, 185, 213, 230, 84, 127, 54, 179, 36, 10, 155, 207, 175, 138, 50], [14, 100, 3, 93, 159, 22, 163, 57, 95, 210, 206, 203, 142, 255, 17, 137, 104]]
RC4KEY = [44, 128, 188, 10, 35, 20]



def getMpdKey(kidraw,userid,usertoken):
    # from string uuid -> byte uuid -> b64_url_nopadding uuid
    kid =urlsafe_b64encode(uuid.UUID(kidraw).bytes).rstrip('=')
    # print "Kid:",kid
    print "kid",uuid.UUID(kidraw).bytes.encode('hex')

    #TODO appversion from app.js
    # appversion <--relate-> RC4KEY DATAS

    res = requests.get("https://api.abema.io/v1/media/token" ,
        params = {"osName":"pc","osVersion":"1.0.0","osLang":"ja_JP","osTimezone":"Asia/Tokyo","appVersion":"v7.0.2" } ,
        headers={"Authorization" :"Bearer "+usertoken})

    mediatoken = res.json()['token']

    #mpd is only supported in pc ,so there's only one kind of license api
    res = requests.post("https://license.abema.io/abematv",params={"t":mediatoken},json={"kids":[kid],"type":"temporary"})
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
        # return final

        print "key:",urlsafe_b64decode(final+"==").encode('hex') #EME use base64(key)
        print '"{0}":"{1}"'.format(uuid.UUID(kidraw).bytes.encode('hex'),urlsafe_b64decode(final+"==").encode('hex') )

    elif second_lastchar == '4':
        raise NotImplementedError
    else:
        raise NotImplementedError


JP_HEADER = {"X-Forwarded-For":"1.0.16.0"}

res = requests.get("https://linear-abematv.akamaized.net/channel/abema-anime/manifest.mpd",headers = JP_HEADER).content
mpdxml = et.fromstring(res)
baseurl = mpdxml.find(".//{{{0}}}BaseURL".format(mpdxml.nsmap[None])).text

adaptset = filter(lambda x: x.attrib.get('mimeType',False)  == 'video/mp4' , mpdxml.findall(".//{{{0}}}AdaptationSet".format(mpdxml.nsmap[None])))[0]

ts = [i.attrib for i in adaptset.find(".//{{{0}}}SegmentTimeline".format(adaptset.nsmap[None])).findall('.//{{{0}}}S'.format(adaptset.nsmap[None]))]

template = adaptset.find(".//{{{0}}}SegmentTemplate".format(adaptset.nsmap[None])).attrib

timescale = int(template['timescale'])

repid = adaptset.find(".//{{{0}}}Representation".format(adaptset.nsmap[None])).attrib['id']

mediatmp = template['media'].replace("$RepresentationID$",repid)

inittmp = template['initialization'].replace("$RepresentationID$",repid)


kid = adaptset.find(".//{{{0}}}ContentProtection".format(adaptset.nsmap[None])).attrib['{urn:mpeg:cenc:2013}default_KID']

getMpdKey(kid,userid,usertoken)

base = int(ts[0].get("t"))

with open("./src/init.m4s",'wb') as f:
	f.write(requests.get(baseurl+inittmp,headers = JP_HEADER).content)


for i in ts:
	rpt = int(i.get("r",0)) # repeat
	for r in range(rpt+1):
		with open("./src/%d.m4s"%(base),'wb') as f:
			f.write(requests.get(baseurl+mediatmp.replace("$Time$",str(base)) ,headers = JP_HEADER).content)
		base += int(i.get("d"))
		time.sleep(int(i.get("d")) *1.0 / timescale)

#then concat and decrypt
