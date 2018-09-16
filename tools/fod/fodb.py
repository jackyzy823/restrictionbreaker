import requests
import lxml.etree as et
import sqlite3
sqlitedb  =sqlite3.connect("fod.db",check_same_thread  =False)
sqlitecur = sqlitedb.cursor()
sqlitecur.execute('create table fodraw (ser text primary key, genre text, json text);') 
# sm = et.fromstring(requests.get('http://fod.fujitv.co.jp/sitemap.xml').content)
# fodurls = [ i.find('./loc',namespaces=sm.nsmap).text for i in sm.findall('./url',namespaces=sm.nsmap)]
# serurls = filter(lambda x : 'ser' in x , fodurls) 
# for i in serurls:                                       
#     genre ,ser = re.match(r'http://.*/genre/(.*?)/ser(.*)/',i).groups()
#     resp = requests.get('https://fod.fujitv.co.jp/api/premium/get_program_view.aspx?lg=1&luid='+ser).content                
#     sqlitecur.execute('insert into fodraw (ser,genre,json) values (?,?,?)',(ser,genre,resp))
#     sqlitedb.commit()         

# more items
urls2 = []
# for i in range(1,44):
i = 1 
while True:
	page = requests.get("http://fod.fujitv.co.jp/s/genre/all?page={0}&s=0".format(i)).content
	if page.find('該当する番組が存在しません')!=-1:
		break
	urls2 += re.findall(r'href="(.*?)" class="lB-wrapLink"',page)
	i+=1

# lg = 0 not login lg =1 login lg=-1...? get more?
for i in urls2:                                       
    genre ,ser = re.match(r'http://.*/genre/(.*?)/ser(.*)/',i).groups()
    resp = requests.get('https://fod.fujitv.co.jp/api/premium/get_program_view.aspx?lg=1&luid='+ser).content.decode('utf-8')              
    sqlitecur.execute('insert or replace into fodraw (ser,genre,json) values (?,?,?)',(ser,genre,resp))
    sqlitedb.commit()  

'''
productid AAAA BB CCCC

80 -> 5141800001 url in page https%3a%2f%2fhls-vod-auth.stream.co.jp%2fhls-vod-auth%2ffod-fms-multi%2fmeta.m3u8%3ftk%3d2ec0b45f4783cac7e7549d85be31274f0a3413f7199f66846e4aa63ae0c0275c035e61e86f5ecc1d70147901a20685bc
11 -> premium 
45 -> 5112450100
01 -> 2121010001
71 -> 5150710001 5150 5153-5156  5149710001
82 -> preview or digest

'''

#fod__program
'''
progra_id
genre -> multi_array ? or genre in sitemap
program_title:
episode_entry : count_of_episodes (shoud update)
program_cast -> string 
program_id primary
program_img_url
program_info
program_overview: introduction
program_staff:
program_img_url http://i.fod.fujitv.co.jp/fodapp/foddoga/thumbnail/a001/a001_main.jpg
(img url is not most clear pic)

CREATE TABLE `downloadinfo`.`fod__program` ( 
`program_id` VARCHAR(16) NOT NULL , 
`genre` VARCHAR(16) NOT NULL , 
`program_title` TEXT NOT NULL , 
`episode_entry` INT NOT NULL , 
`program_info` TEXT NULL , 
`program_overview` TEXT NULL , 
`program_cast` TEXT NULL , 
`program_staff` TEXT NULL , 
`program_img_url` TEXT NOT NULL , 
PRIMARY KEY (`program_id`)) ENGINE = InnoDB; 

episodes:
'''
#fod__episode
'''
display_order 
end_day 
episode_img_url
episode_time
episode_story introduction
productid
sub_title
icon_ free/addnew/freetalk/new/premiere ?
'''

#m3u8 = filter(lambda x : x.find("me113")!=-1 ,requests.get("https://i.fod.fujitv.co.jp/abr/pc_html5/{0}.m3u8".format(publisher_id)).content.split("\r\n"))[0]

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
