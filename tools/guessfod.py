# import requests
import string
from itertools import product
import time
import random
start = time.time()
print "start ",start

import socket



from multiprocessing.dummy import Pool

# s =requests.session()#for reuse http connection
# adapter = requests.adapters.HTTPAdapter(pool_connections=SIZE, pool_maxsize=SIZE)
# s.mount('http://', adapter)

p = None

#use http replace https to reduce traffic
def worker(a):
    if s.head('%s%s%s%s.mp4.m3u8'%a).status_code!=404:
        print '%s%s%s%s.mp4.m3u8'%a
        print "find ",time.time()

def worker2(a):
		addr = ["202.247.51.61","202.247.51.62","202.247.51.70","202.247.51.71"][(ord(a[0])+ord(a[1]))%4]
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((addr, 80))
		for v in product(string.lowercase+string.digits,repeat=2):
			s.sendall("HEAD /www08/fod-plus7/phls/video/01234/4f07/4f07810006me113%s%s%s%s.mp4.m3u8 HTTP/1.1\r\nConnection:Keep-Alive\r\nHost:136ea006abc838d0070ae4bde485da88.cdnext.stream.ne.jp\r\n\r\n"%(a[0],a[1],v[0],v[1]))
			data = s.recv(1024)
			if data[9:12] != '404':
				print "%s%s%s%s"%(a[0],a[1],v[0],v[1])
				print "end ",time.time()
				print "dur ",time.time() - start
				p.close()
				p.terminate()
		s.close()


p = Pool(36*36)
res = p.imap_unordered(worker2,product(string.lowercase+string.digits,repeat=2))
for i in res:
    pass
