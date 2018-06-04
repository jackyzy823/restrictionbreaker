import requests
import string
from itertools import product
import time
print "start ",time.time()

from multiprocessing.dummy import Pool
s =requests.session()#for reuse http connection 
#use http replace https to reduce traffic
def worker(a):
    if s.get('%s%s%s%s.mp4.m3u8'%a).status_code!=404:
        print '%s%s%s%s.mp4.m3u8'%a
        print "find ",time.time()

p = Pool(50)
res = p.imap(worker,product(string.lowercase+string.digits,repeat=4))
for i in res:
    pass
