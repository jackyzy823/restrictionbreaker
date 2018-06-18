import requests
from Crypto.Cipher import AES
from multiprocessing.dummy import Pool


url = "https://136ea006abc838d0070ae4bde485da88.cdnext.stream.ne.jp/www08/fod-plus7/phls/video/01234/4f07/4f07810008me113e028.mp4.m3u8"
tsurl = "/".join(url.split("/")[:-1])
m3u8 = requests.get(url).content
tss = filter( lambda x : not x.startswith('#') and x!='',m3u8.split('\r\n'))
keyurl = filter( lambda x : x.startswith('#EXT-X-KEY') ,m3u8.split('\r\n'))[0]
import re

key = re.findall(r"\"(.*?)\"",keyurl)[0]
method = re.findall(r'METHOD=(.*?),',keyurl)[0]
iv = re.findall(r'IV=(.*)',keyurl)[0]
keydata = requests.get(key).content

def worker(i):
	a = AES.new(keydata,AES.MODE_CBC,iv[2:].decode('hex'))
	d = requests.get(tsurl+i).content
	res = a.decrypt(d)
	res = res[ :-1*ord(res[-1])]
	with open(i,'wb') as f : 
		f.write(res)

p = Pool(10)
p.map(worker,tss)
