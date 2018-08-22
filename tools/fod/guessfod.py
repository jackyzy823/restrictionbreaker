# import requests
import string
from itertools import product
import time
import random
start = time.time()
print "start ",start

import socket
letters = string.lowercase+string.digits


from multiprocessing.dummy import Pool,Manager

# s =requests.session()#for reuse http connection
# adapter = requests.adapters.HTTPAdapter(pool_connections=SIZE, pool_maxsize=SIZE)
# s.mount('http://', adapter)

ips = ["101.102.235.60","101.102.235.61","101.102.235.62" ,"101.102.235.70","101.102.235.71","101.102.235.72",
        "111.108.184.60","111.108.184.61","111.108.184.62","111.108.184.70","111.108.184.71","111.108.184.72",
        "202.247.51.60","202.247.51.61","202.247.51.62" , "202.247.51.70","202.247.51.71" ,"202.247.51.72" ,
        "202.79.241.60", "202.79.241.61", "202.79.241.62", "202.79.241.70", "202.79.241.71", "202.79.241.72",
        "27.121.48.60","27.121.48.61","27.121.48.62","27.121.48.70","27.121.48.71","27.121.48.72"
]

cip = len(ips)
req = 'HEAD /www08/fod-plus7/phls/video/01234/4f14/4f14810001me113%s%s%s%s.mp4.m3u8 HTTP/1.1\r\nHost:136ea006abc838d0070ae4bde485da88.cdnext.stream.ne.jp\r\n\r\n'

def worker2(a):
    addr  =  ips[random.randint(0,cip-1)]
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((addr, 80))
    for v in product(string.lowercase+string.digits,repeat=2):
        while True:
            s.sendall(req%(a[0],a[1],v[0],v[1]))
            data = s.recv(1024)
            if data[9:12] != '404' and data[9:12] == '200':
                print req%(a[0],a[1],v[0],v[1])
                print "end ",time.time()
                print "dur ",time.time() - start
                s.close()
                return True
            elif data[9:12] != '404':
                if len(data) == 0:
                    time.sleep(1)
                else:
                    print "stauscode: %s, at :%s  ->%s%s%s%s "%(data[9:12],addr,a[0],a[1],v[0],v[1] )
                    break
            else:
                break #ext


        s.close()
        return False

# ulimit open file -> increse 
# stack size -> decrese
p = Pool(36*36)


#p.map_async(worker2,letters,callback = lambda x: p.terminate() if x else None)
for i in product(string.lowercase+string.digits,string.lowercase+string.digits):
    p.apply_async(worker2,(i,),callback = lambda x: p.terminate() if x else None)
p.close()
p.join()
print "done"

