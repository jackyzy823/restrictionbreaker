from abema import generateUserInfo
import requests
(userid,deviceid,usertoken) = generateUserInfo()

s = requests.session()
s.headers.update({"Authorization":"Bearer "+usertoken ,"User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",})

import json



import sqlite3

db  =sqlite3.connect("db_abemavideo.db",check_same_thread  =False)
cur = db.cursor()
cur.execute(
'''CREATE TABLE IF NOT EXISTS `abemavideo` (
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
);''')






genres = s.get("https://api.abema.io/v1/video/genres",headers = {"Authorization":"Bearer "+usertoken}).json()["genres"]
interested = ['reality','animation','drama','reality','documentary','movie', 'music']

for genre in interested:
    print genre
    cards = []
    next_ = ''
    while True:
        respj = s.get("https://api.abema.io/v1/video/featureGenres/{0}/cards?limit=20&next={1}&onlyFree=false".format(genre,next_)).json()
        cards += respj["cards"]
        if respj['paging'].get("next","") == '':
            break
        else:
            next_ = respj['paging']['next']
    for item in cards:
        #series scope
        seriesId = item['seriesId']
        print "\r{0:<60}".format(seriesId),
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
            print "\r{0},{1:<40}".format(season_id,seriesId),
            offset = 0
            programs = []
            while True:
                resp = s.get("https://api.abema.io/v1/video/series/{0}/programs?limit=20&offset={1}&order=seq&seasonId={2}&seriesVersion={3}".format(seriesId,offset,season_id,version))
                tmp_prgs = resp.json()["programs"]
                if len(tmp_prgs) == 0:
                    break
                offset +=20
                programs += tmp_prgs
            for prg in programs:
                prgid = prg["id"] #unique id
                print "\r{0},{1},{2:<20}".format(prgid,season_id,seriesId),
                duration = prg["info"]["duration"]

                credit = json.dumps(prg["credit"]) #json {cast,released,copyrights,crews}
                endAt = prg["endAt"]
                #TODO label is episode free
                if prg["label"].get("free"):
                    prg_freeendat = prg["freeEndAt"]
                else:
                    prg_freeendat = None
                # if label -> free:true ->  prg["freeEndAt"]
                prg_title = prg["episode"]["title"] # filename
                prg_content = prg["episode"]["content"]
                prg_num = prg["episode"]["number"]
                transcodeVersion = prg["transcodeVersion"]
                respj = s.get("https://api.abema.io/v1/video/programs/{0}".format(prgid)).json()
                hls = respj["playback"]["hls"]
                if len(respj["playback"])>1:
                    print respj["playback"]
                cur.execute("INSERT OR IGNORE INTO abemavideo (`prg_id`, `prg_title`, `series_id`, `series_title`  , `series_caption` , `series_content` , `season_id` , `season_title` , `genre`, `prg_content` , `prg_num`  , `prg_duration` , `prg_credit`  , `prg_endat`, `prg_freeendat` , `prg_url`) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);",
                    (prgid , prg_title , seriesId, series_title, caption, series_content, season_id ,season_name ,genre, prg_content,prg_num , duration, credit,endAt , prg_freeendat , hls ))
                db.commit()
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