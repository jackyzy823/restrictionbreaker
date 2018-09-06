import requests
import re
sess = requests.session()
from requests.adapters import HTTPAdapter
adapter = HTTPAdapter(pool_maxsize=200,max_retries=5) # max retry for cx connectionerror
sess.mount("http://", adapter)
sess.mount("https://", adapter)
# import sqlite3

# db  =sqlite3.connect("db_tver.db",check_same_thread  =False)
# cur = db.cursor()
# cur.execute(
# '''CREATE TABLE if not exists `tver`  (
#     `reference_id`  TEXT NOT NULL,
#     `service`   TEXT NOT NULL,
#     `player_id` TEXT NOT NULL,
#     `name`  TEXT NOT NULL,
#     `title` TEXT,
#     `subtitle`  TEXT,
#     `catchup_id`    TEXT,
#     `url`   TEXT,
#     `service_name`  TEXT,
#     `id`    TEXT NOT NULL,
#     `json`  TEXT,
#     `updated_at` TIMESTAMP,
#     `done` BOOL,
#     UNIQUE (reference_id,player_id,id)
# );''')
import sys
import mysql.connector
dbconfig = {
    "user":"downloadinfo",
    "password":"downloadinfo",
    "host":"127.0.0.1",
    "database":"downloadinfo"
}

db = None
try:
    db = mysql.connector.connect(**dbconfig)
except mysql.connector.Error,err:
    sys.exit(err.errno)
cur = db.cursor()

'''
CREATE TABLE `downloadinfo`.`tver` ( `rowid` INT NOT NULL AUTO_INCREMENT ,
 `reference_id` VARCHAR(255) NOT NULL ,
 `service` VARCHAR(15) NOT NULL ,
 `player_id` VARCHAR(255) NOT NULL ,
 `name` TEXT NOT NULL ,
 `title` TEXT NULL ,
 `subtitle` TEXT NULL ,
 `catchup_id` TEXT NULL ,
 `url` TEXT NULL ,
 `service_name` TEXT NULL ,
 `id` VARCHAR(255) NOT NULL ,
 `json` text NULL ,
 `updated_at` varchar(32) NULL DEFAULT NULL ,
 `done` TINYINT NOT NULL DEFAULT '0' ,
 PRIMARY KEY (`rowid`)) ENGINE = InnoDB;
 ALTER TABLE `tver` ADD UNIQUE( `reference_id`, `player_id`, `id`);

'''

'''
/corner/
/episode/
/feature/
'''

pagepattern = re.compile(r'''addPlayer\(\s*?'(?P<player_id>.*?)',\s*?'(?P<player_key>.*?)',\s*?'(?P<catchup_id>.*?)',\s*?'(?P<publisher_id>.*?)',\s*?'(?P<reference_id>.*?)',\s*?'(?P<title>.*?)',\s*?'(?P<subtitle>.*?)',\s*?'(?P<service>.*?)',\s*?'(?P<servicename>.*?)',''')

policykeypattern = re.compile(r'''catalog\(\{accountId:\"?(?P<accountId>.*?)\"?,policyKey:\"(?P<policyKey>.*?)\"''')

BCOV_POLICY = {
#YTV
 "5330942432001":"BCpkADawqM0kGrWxZoXJvJj5Uv6Lypjp4Nrwzz1ktDAuEbD1r_pj0oR1900CRG04FFkxo0ikc1_KmAlB4uvq_GnFwF4IsG_v9jhYOMajC9MkdVQ-QrpboS7vFV8RvK20V5v-St5WGPfXotPx",
#TX
 "3971130137001":"BCpkADawqM1F2YPxbuFJzWtohXjxdgDgIJcsnWacQKaAuaf0gyu8yxCQUlca9Dh7V0Uu_8Rt5JUWZTpgcqzD_IT5hRVde8JIR7r1UYR73ne8S9iLSroqTOA2P-jtl2EUw_OrSMAtenvuaXRF",
#TBS
 "4031511847001":"BCpkADawqM1n_azNkrwm-kl2UhijTLt4W7KZ6KS9HluAoLPvyRFu2X4Xu2dUuW-lLOmc6X7WjsiBwh83m8ecNmxl-pVy9w3M9iI6-en-_wIDvNJixpoMf4BhdOPtwO_7XIol9P3wVrq2BIzw",
 "4394098881001":"BCpkADawqM3m-3484dphPL5raj3jQJVlFecOYAvpxhtJaK99BVRKtxd9SC6q0kOsknI1FD3kplVUaJzneAQb55EkCcDHrD9m_yoesmjsIfJpKQXJKfmQ5LfAFJnmf2Sv48heP_R1PGznwbAn",
#NTV
 "4394098882001":"BCpkADawqM1s6XkqRoC2a0eEORY7FFF780eHkHQZ93Fw752A9swymrSMZEVF1d7G3mSby3Etzj8MGJp_ZwXpbSTH1ApfZxZ1FSPQ4LXDQhpaMRADtCbxKFTpAxGYwN61DYKKksmg4uwcdhLD",
#MBS
 "5102072605001":"BCpkADawqM1VhDl0FtgrrM8jB-hVNkcrdrx4x9C_60OSeN4jIHynGkIKw0PY1cOsRqQYJOnJRscPAbdPTcpzZ_4g89Gcte_yQFW-yeWxzrPECulIh9ZlaZsJ_3rH7Gjs_RnuWHx_lTzilaxh",
#KTV
 "5718741494001":"BCpkADawqM1llDtMelQ9nQyE91bAc-E5T1B0135MCCRZ_o4FlDkGWQY8t8Nrt1fJKAgui-kLefX-JGaRItrDXh_C1GlIgCSv-rhNPQYKJsY8nZp_IoJ38Mf3B5BSJLFulW0QhgQduipc9j4D",
#EX no publisherid
 "4031511847001":"BCpkADawqM2N0e6IdrmQn-kEZJ0jRi-Dlm0aUZ9mVF2lcadunJzMVYD6j_51UZzQ3mXuIeV8Zx_UUvbGeeJn73SSrpm0xD7qtiKULPP2NEsp_rgKoVxVWTNZAHN-JAHcuIpFJT7PvUj6gpZv",
#ABC   
 "5102072603001":"BCpkADawqM2NfzEA47jZiJNK0SYahFenNwAtoehfrIAaCqxmHjBidnt_YfvFnp5j-Zi58FPj-zXAHATYU1nnOOuEf9XXV8JRGYSuZ5dgyNc2RjGv2Ej5zGfhxWs3_p4F7huxtbAD9fzQlg7b",
#World cup
 "5764318572001":"BCpkADawqM3KJLCLszoqY9KsoXN2Mz52LwKx4UXYRuEaUGr-o3JBSHmz_0WRicxowBj8vmbGRK_R7Us96DdBYuYEoVX9nHJ3DjkVW5-8L6bRmm6gck8IaeLLw21sM6mOHtNs9pIJPF6a4qSZlO6t_RlkpMY6sasaIaSYlarJ_8PFMPdxxfY6cGtJDnc"
}

def dbCommit(datatuple):
    try:
        cur.execute("insert ignore into tver (`reference_id` , `service` , `player_id` , `name` , `title` , `subtitle` , `catchup_id` , `url` , `service_name` , `id` , `json` , `updated_at` , `done`) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0);",
        datatuple);
        #set innodb_autoinc_loc_mode=0
    except mysql.connector.errors.IntegrityError:
        pass
        # print "duplicate: {0}: {1}".format(datatuple[1],datatuple[7])
    db.commit()


def parsePage(url):
    res = pagepattern.search(sess.get(url).content)
    if not res:
        raise ValueError(url)
    resdict = res.groupdict()

    service = resdict["service"]
    servicename = resdict["servicename"]
    publisher_id = resdict['publisher_id']
    catchup_id = resdict['catchup_id']
    title = resdict["title"]
    title = title.decode("utf-8").strip(u'\u3000').strip().encode("utf-8")

    subtitle = resdict["subtitle"]
    subtitle = subtitle.decode("utf-8").strip(u'\u3000').strip().encode("utf-8")
    #.strip(u'\u3000').strip()

    if service == 'cx':
        # id = publisher_id
        player_id = ''
        player_key = ''
        reference_id = ''

        #PUBLISHERID (like 4f50810003) FOR CX 
        if len(publisher_id) == 4:
            #sample 5645
            infoapi = "https://i.fod.fujitv.co.jp/plus7/web/{0}.html".format(publisher_id)
            resp = sess.get(infoapi)

        else:
            infoapi = "https://i.fod.fujitv.co.jp/plus7/web/{0}/{1}.html".format(publisher_id[0:4],publisher_id)
            resp = sess.get(infoapi)

        # print "url for cx :{0}".format(url)
        #https://i.fod.fujitv.co.jp/plus7/web/ + publisher_id[0:4]+"/"+publisher_id+".html"
        #TODO & FIX: fod use now kind of url: https://i.fod.fujitv.co.jp/abr/pc_html5/<videoid>.m3u8 or https://i.fod.fujitv.co.jp/abr/pc_flash/<video>.m3u8
        #if expired this url display nothing! so we need raw !
        try:
            name = re.findall(r'_wa\.parameters\[ \'title\' \] = \'(.*)\';',resp.content)[0].strip().decode('utf-8')
        except:
            print "url for cx :{0},{1} name not found".format(url,infoapi)
            name = ""

        mediaid = re.findall(r'mediaid=(.*?)\"',resp.content)[0]

        if len(publisher_id)==4:
            publisher_id = mediaid
        assert(mediaid == publisher_id)
        m3u8 = filter(lambda x : x.find("me113")!=-1 ,requests.get("https://i.fod.fujitv.co.jp/abr/pc_html5/{0}.m3u8".format(publisher_id)).content.split("\r\n"))[0]

        if len(subtitle) ==0:
            resp = sess.get("http://fod-sp.fujitv.co.jp/s/tver/redir.aspx?ser={0}".format(publisher_id))
            if resp.url.find("error")!=-1:
                #for those pasts -> 
                subtitle = publisher_id[-4:]
            else:
                subtitle = re.findall(r'''episode-title\">\s*?<h3>(.*?)</h3>''',resp.content)[0].replace('\xe3\x80\x90\xe7\x84\xa1\xe6\x96\x99\xe3\x81\xe3\x80\x91','').strip()


        return (reference_id,
                service,
                player_id,
                name.replace("/","_"),
                title.replace("/","_").decode("utf-8").strip(u'\u3000').strip(),
                subtitle.replace("/","_").decode("utf-8").strip(u'\u3000').strip(),
                catchup_id,
                url,
                servicename.decode("utf-8"),
                publisher_id,
                m3u8,
                None)

        # raise ValueError("url for tx :{0}".format(url))

    if service != 'tx':
        reference_id = "ref:"+resdict['reference_id']
    else:
        reference_id = resdict['reference_id']

    player_id = resdict['player_id'] #is also accountid
    player_key = resdict['player_key']

    infoapi = "https://players.brightcove.net/{0}/{1}_default/index.min.js".format(player_id,player_key)
    res = policykeypattern.search(sess.get(infoapi).content)
    if not res:
        print infoapi
        policyKey = BCOV_POLICY[player_id]
        #use default?
    else:
        resdict = res.groupdict()
        policyKey = resdict['policyKey']

    playinfoapi = "https://edge.api.brightcove.com/playback/v1/accounts/{0}/videos/{1}".format(player_id,reference_id)
    res = sess.get(playinfoapi,headers = {"X-Forwarded-For":"1.0.16.0","Accept":"application/json;pk={0}".format(policyKey)})
    resj = res.json()
    # import pdb;pdb.set_trace()
    return (reference_id,
            service,
            player_id,
            resj['name'].replace("/","_"),
            title.replace("/","_").decode("utf-8").strip(u'\u3000').strip(),
            subtitle.replace("/","_").decode("utf-8").strip(u'\u3000').strip(),
            catchup_id,
            url,
            servicename.decode("utf-8"),
            resj["id"],
            res.content.decode("utf-8") ,
            resj["updated_at"])
    #source
    #res["name"] 
    # "published_at"
    # "duration published_at updated_at created_at
    # id is the realid

linkPattern = re.compile(r'''(\/episode\/.*?)\/?\"|(\/corner\/.*?)\/?\"|(\/feature\/.*?)\/?\"''')

def filter_finish(urls): #set
    return urls
    # cur.execute("select url from tver where url in ("+",".join("?"*len(urls))+");",tuple(urls))
    # m_url = map(lambda x : x[0] , cur.fetchall())
    # return urls - set(m_url)

def findAll():
    count = 0
    for url in ("/","/ranking", "/soon", "/drama", "/variety", "/documentary", "/anime", "/sport", "/other"):
        page = sess.get("https://tver.jp{0}".format(url)).content
        urls = linkPattern.findall(page)
        links = filter_finish(set(map(lambda x : "https://tver.jp{0}".format(filter (lambda y:y ,x)[0]) ,urls))) #without right /
        count+=len(links)
        for i in links:
            try:
                dbCommit(parsePage(i))
            except Exception as e:
                import traceback
                traceback.print_exc()
                print str(e)
                print i
    return count

def findAllByBrand():
    count = 0
    for svc in ("tbs","tx", "ex", "ntv", "cx", "ktv", "mbs", "abc", "ytv"):
        page = sess.get("https://tver.jp/{0}".format(svc)).content
        urls = linkPattern.findall(page)
        links = filter_finish(set(map(lambda x : "https://tver.jp{0}".format(filter (lambda y:y ,x)[0]) ,urls))) #without right /
        count += len(links)
        for i in links:
            try:
                dbCommit(parsePage(i))
            except Exception as e:
                import traceback
                traceback.print_exc()
                print str(e)
                print i
    return count

def findAllBySitemap():
    def lp2url(lp):
        try:
            page = sess.get(lp).content
            res = re.search(r'location\.href="(.*)"',page).groups()[0]
            return "http://tver.jp{0}".format(res)
        except:
            print "err lp:{0}".format(lp)
            return ""

    import lxml.etree as et
    from multiprocessing.dummy import Pool
    sm =  et.fromstring( sess.get("https://tver.jp/sitemap.xml").content )
    tverurls = [ i.find('./loc',namespaces=sm.nsmap).text for i in sm.findall('./url',namespaces=sm.nsmap)][1:] #jump index
    lp = filter( lambda x: x.find("/lp/") != -1 , tverurls ) 
    p = Pool(50)
    lurls = p.map(lp2url,lp)
    urls = filter( lambda x: all( map(lambda y:  x.find(y) == -1,["/lp/","/talent/","/ranking/","/soon/","/search/","/mylist/","/topics/","/info/"] ) ) , tverurls ) 

    print set(lurls) - set(urls)
    for i in set(urls) | set(lurls):
        try:
            dbCommit(parsePage(i))
        except Exception as e:
            import traceback
            traceback.print_exc()
            print str(e)
            print i
    return len(set(urls) | set(lurls))


res = findAll()
print "Category->pages: {0}",res
cur.execute("select count(*) from tver where done=0 limit 1;")
res = cur.fetchone()
print "New task:",res[0]
res = findAllByBrand()
print "Brand->pages: {0}",res
cur.execute("select count(*) from tver where done=0 limit 1;")
res = cur.fetchone()
print "New task:",res[0]
res = findAllBySitemap()
print "Sitemap->pages: {0}",res
cur.execute("select count(*) from tver where done=0 limit 1;")
res = cur.fetchone()
print "New task:",res[0]