from abema import generateUserInfo,getM3u8Key
import requests
(userid,deviceid,usertoken) = generateUserInfo()

s = requests.session()
s.headers.update({"Authorization":"Bearer "+usertoken ,"User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",})

from requests.adapters import HTTPAdapter
adapter = HTTPAdapter(pool_maxsize=200,max_retries=5)
s.mount("http://", adapter)
s.mount("https://", adapter)
from multiprocessing.dummy import Pool
p = Pool(50)

import json
import sys

# from  backports.shutil_get_terminal_size import get_terminal_size

# import sqlite3

# db  =sqlite3.connect("db_abemavideo.db",check_same_thread  =False)
# cur = db.cursor()
# cur.execute(
# '''CREATE TABLE IF NOT EXISTS `abemavideo` (
#     `prg_id`   TEXT  PRIMARY KEY NOT NULL,
#     `prg_title` TEXT,
#     `series_id` TEXT NOT NULL,
#     `series_title`  TEXT NOT NULL,
#     `series_caption`    TEXT,
#     `series_content`    TEXT,
#     `season_id` TEXT NOT NULL,
#     `season_title`  TEXT,
#     `prg_content`   TEXT,
#     `genre`     TEXT,
#     `prg_num`   INTEGER,
#     `prg_duration`  INTEGER,
#     `prg_credit`    TEXT,
#     `prg_endat` TIMESTAMP NOT NULL,
#     `prg_freeendat` TIMESTAMP,
#     `prg_url`   TEXT,
#     `done`  INTEGER DEFAULT 0,
#     `video_key` VARCHAR(32)
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
cur = db.cursor(buffered=True)


#done 0
#    1  finished
#   -1  expired
#   -2  downloaderror?
#   -3  has drm


#abema.reality 1qazXSW@ Sh Bj Tk Kt Ngy


'''
if time > prg_endat , you can do nothing
if prg_endat > time > prg_freeendat and has video_key still can download by passing video_key  or premium
if time < prg_freeendat  direct download and save video_key for `time > prg_freeendat`
 
'''

# genres = s.get("https://api.abema.io/v1/video/genres",headers = {"Authorization":"Bearer "+usertoken}).json()["genres"]
interested = ['documentary', 'music' ,'reality','animation','drama','variety','movie' ] #
new_count = 0

def test(prg):
    prgid = prg["id"] #unique id
    # sys.stderr.write("\r{0:<{1}}".format("{0},{1},{2}".format(prgid,season_id,seriesId),get_terminal_size().columns))
    # sys.stderr.flush()
    duration = prg["info"]["duration"]

    credit = json.dumps(prg["credit"]) #json {cast,released,copyrights,crews}
    endAt = int(prg["endAt"])
    #TODO label is episode free
    if prg["label"].get("free"):
        prg_freeendat = int(prg["freeEndAt"])
    else:
        prg_freeendat = None
    # if label -> free:true ->  prg["freeEndAt"]
    prg_title = prg["episode"]["title"] # filename
    prg_content = prg["episode"]["content"]
    prg_num = prg["episode"]["number"]
    transcodeVersion = prg["transcodeVersion"]
    respj = s.get("https://api.abema.io/v1/video/programs/{0}".format(prgid)).json()
    hls = respj["playback"]["hls"]
    done = 0
    if respj["playback"].get("dash",None):
        done = -3
    # if get dash -> then hls may pr enc and sample video how to?
    video_key = None
    if prg_freeendat and done == 0 :
        hls1080 = hls.split("/")
        hls1080.insert(-1,"1080")
        try:
            video_key = getM3u8Key("/".join(hls1080),deviceid,userid,usertoken )
        except:
            #those need pr in hls or expired?
            pass
    return (prgid,prg_title,prg_content,duration,credit,endAt,prg_freeendat,prg_num,hls,video_key,done)

for genre in interested:
    print "\n",genre
    cards = []
    next_ = ''
    while True:
        respj = s.get("https://api.abema.io/v1/video/featureGenres/{0}/cards?limit=100&next={1}&onlyFree=false".format(genre,next_)).json()
        cards += respj["cards"]
        if respj['paging'].get("next","") == '':
            break
        else:
            next_ = respj['paging']['next']

    for item in cards:
        #series scope
        seriesId = item['seriesId']
        # sys.stderr.write("\r{0:<{1}}".format(seriesId,get_terminal_size().columns))
        # sys.stderr.flush()
        title = item['title']
        caption = item.get('caption',None)
        if item["label"].get("someFree"):
            freetype = "someFree"
        elif item["label"].get("free"):
            freetype = "free"

        # print seriesId,title,caption,freetype
        programProvidedInfo = item['programProvidedInfo']
        if len(programProvidedInfo.keys())!=0:
            print "Having providedInfo",seriesId,title
        resp = s.get("https://api.abema.io/v1/video/series/{0}".format(seriesId))
        respj = resp.json()
        seasons = respj["seasons"]
        orderedseasons = respj["orderedSeasons"]
        version = respj["version"]
        series_content = respj["content"]
        series_title = respj["title"]
        assert(series_title == title)

        #TODO seasons = None
        if orderedseasons == None:
            orderedseasons = [{"name":None,"id": seriesId+"_s0"}]
        for odseason in orderedseasons:
            season_name = odseason["name"] #sub folder name
            season_id = odseason["id"]
            # sys.stderr.write("\r{0:<{1}}".format("{0},{1}".format(season_id,seriesId),get_terminal_size().columns))
            # sys.stderr.flush()
            offset = 0
            programs = []
            _limit = 100
            while True:
                resp = s.get("https://api.abema.io/v1/video/series/{0}/programs?limit={4}&offset={1}&order=seq&seasonId={2}&seriesVersion={3}".format(seriesId,offset,season_id if season_name is not None else '',version , _limit))
                tmp_prgs = resp.json()["programs"]
                if len(tmp_prgs) == 0:
                    break
                offset += 100
                programs += tmp_prgs
            ress = p.map(test , programs)
            for res in ress:
                (prgid,prg_title,prg_content,duration,credit,endAt,prg_freeendat,prg_num,hls,video_key,done)  = res
                try:
                    #OR IGNORE
                    cur.execute("INSERT INTO abemavideo (`prg_id`, `prg_title`, `series_id`, `series_title`  , `series_caption` , `series_content` , `season_id` , `season_title` , `genre`, `prg_content` , `prg_num`  , `prg_duration` , `prg_credit`  , `prg_endat`, `prg_freeendat` , `prg_url`,`video_key` ,`done`) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",
                    (prgid , prg_title , seriesId, series_title, caption, series_content, season_id ,season_name ,genre, prg_content,prg_num , duration, credit,endAt , prg_freeendat , hls ,video_key ,done))
                    new_count +=1 # 
                except mysql.connector.errors.IntegrityError as e:
                    if e.errno == 1062:
                        cur.execute("SELECT `prg_id`, `prg_endat`, `prg_freeendat`, `video_key` from abemavideo where `prg_id` = %s;", (prgid,))
                        res = cur.fetchone()
                        old_end = res[1]
                        old_freeendat = res[2]
                        old_video_key = res[3]

                        # if old_freeendat != prg_freeendat:
                        # do not update freeend -> none , just let expried freendat exists. to check if it has been freed!
                        if video_key != '' and video_key is not None:
                            cur.execute("update abemavideo set `video_key` = %s where prg_id = %s ;" , (video_key,prgid))
                        if prg_freeendat is not None and prg_freeendat > old_freeendat:
                            print "Freeend  Longer! {0} from {1} ---> {2}".format(prgid,old_freeendat,prg_freeendat)
                            cur.execute("update abemavideo set `prg_freeendat` = %s  where prg_id = %s ;" , (prg_freeendat,prgid))
                        if endAt is not None and endAt > old_end:
                            print "End      Longer! {0} from {1} ---> {2}".format(prgid,old_end,endAt)
                            cur.execute("update abemavideo set `prg_endat` = %s where prg_id = %s ;" , (endAt,prgid))
                        if endAt is not None and endAt < old_end:
                            # those expired will not in json so what ever
                            print "End      shortened! {0} from {1} ---> {2}".format(prgid,old_end,endAt)
                            cur.execute("update abemavideo set `prg_endat` = %s where prg_id = %s ;" , (endAt,prgid))
                        if prg_freeendat is not None and prg_freeendat < old_freeendat:
                            # those free expired will be None and not comparable and whatever
                            print "Freeend  shortened! {0} from {1} ---> {2}".format(prgid,old_freeendat,prg_freeendat)
                            cur.execute("update abemavideo set `prg_freeendat` = %s  where prg_id = %s ;" , (prg_freeendat,prgid))
                    else:
                        raise e
                finally:
                    db.commit()

print "\nNew items count:{0}".format(new_count)
                #other format playback?
'''db struct1
table series
series_id
series_title
series_caption 

table seasons
season_id
season_name
series_id



'''


'''db struct
prg_id text
prg_title text --name

series_id text
series_title text  -- folder
series_caption text
series_content text

season_id
season_title --subfolder may be none

prg_content
prg_num
prg_duration
prg_endat
prg_freeendat
prg_credit
prg_url
done

'''
'''
CREATE TABLE IF NOT EXISTS `abemavideo` (
    `prg_id`    TEXT NOT NULL,
    `prg_title` TEXT,
    `series_id` TEXT NOT NULL,
    `series_title`  TEXT NOT NULL,
    `series_caption`    TEXT,
    `series_content`    TEXT,
    `season_id` TEXT NOT NULL,
    `season_title`  TEXT,
    `prg_content`   TEXT,
    `genre`     TEXT,
    `prg_num`   INTEGER,
    `prg_duration`  INTEGER,
    `prg_credit`    TEXT,
    `prg_endat` TIMESTAMP NOT NULL,
    `prg_freeendat` TIMESTAMP,
    `prg_url`   TEXT,
    `done`  INTEGER DEFAULT 0
);

on duplicate update freeendat ...

'''

#         if not seasons and not orderedseasons:
#             print "no seasons",seriesId
#             continue
#         if len(seasons)!= len(orderedseasons):
#             print "seasons",seasons,"orderedseasons",orderedseasons
#         if len(seasons) > len(max_len_seasion):
#             max_len_seasion = seasons

# print max_len_seasion

        

'''
news
variety  *
animation *
drama *
asia
kpop
reality *
documentary *
mahjon
shogi
fishing
fightingsports
hobby
movie *
sports
hiphop
game
music *
ldh
'''