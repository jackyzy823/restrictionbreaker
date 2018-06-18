import requests
from pyquery import PyQuery as pq
import sqlite3
import re
db  =sqlite3.connect("fod.db",check_same_thread  =False)
cur = db.cursor()
cur.execute("create table if not exists fod (vid varchar(10) primary key, serialname text, serialid varchar(4), episode int,m3u8link text ) ;")


res = requests.get('http://fod.fujitv.co.jp/s/genre/drama/?s=2#')
c = pq(res.content)
a = c.find('.icoFree').parent().parent().parent()
u = [i.attr('href') for i in a.items()]

for i in a.items():
	p = requests.get(i.attr('href') ) 
	for j in pq(p.content).find(".btn-free").items():
		try:
			vid = j.attr('onclick').split('/')[-2]
			resp = requests.get("https://i.fod.fujitv.co.jp/plus7/web/%s/%s.html"%(vid[:4],vid))
			if resp.status_code ==404:
				print vid,"not found ? may pv"
				continue
			name = re.findall(r'_wa\.parameters\[ \'title\' \] = \'(.*)\';',resp.content)[0].decode('utf-8')
			meta = re.findall(r'else.*?{.*?meta = \'(.*?)\';',resp.content,re.S)[0]
			m3u8 = re.findall(r'url: "(.*?)",',resp.content)[0].replace('" + meta + "',meta)
			eps = int(vid[-1])
			serid = vid[:4]
			cur.execute("insert or ignore into fod (vid,serialname,serialid,episode,m3u8link) values(?,?,?,?,?);" ,(vid,name,serid,eps,m3u8))
		except Exception,e:
			print  i.attr('href') , e.message
