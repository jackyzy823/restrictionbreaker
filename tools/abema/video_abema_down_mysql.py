#coding:utf-8
import os
import os.path
import subprocess
import time
# import sqlite3
import random
import netaddr

JAPANIPS = netaddr.IPNetwork('43.0.0.0/9')

'''
done = 2 working lock
done = 0  not started
done = 1 finished
done = -1 expired!
done = -2 unchecked error
'''
# db  =sqlite3.connect("db_abemavideo.db",check_same_thread  =False)
# cur = db.cursor()
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
except mysql.connector.Error, err:
    sys.exit(err.errno)
cur = db.cursor(buffered=True) #for get all but fetchone


last = None
dynamic_day = 1
while True:
    starttime = int(time.time())
    cur.execute("select count(*) from abemavideo where done = 0 and prg_freeendat > %s and prg_freeendat is not null and prg_freeendat < %s  ;",(starttime,starttime +dynamic_day * 24 * 60 *60))
    cnt = cur.fetchone()[0];
    if cnt == 0:
        print "no content in {0} days".format(dynamic_day)
        dynamic_day += 1
    for genre in ('reality','animation','drama','variety','documentary','movie', 'music'):
        if genre == last:
            print "Only this site!!!!"
            time.sleep(60*2.5) #same site
        cur.execute("select genre from abemavideo where prg_freeendat > UNIX_TIMESTAMP(CURRENT_TIMESTAMP) and prg_freeendat < UNIX_TIMESTAMP(CURRENT_TIMESTAMP) + 24*60*60 and done=0 group by genre;")
        res = [g[0] for g in  cur.fetchall()]
        if len(res) > 0 and  genre not in res:
            print "More important tasks!"
            dynamic_day = 1
            continue
        cur.execute("select  `prg_id` , `prg_title` , `series_title` , `season_title` , `prg_freeendat`  , `prg_url`  from abemavideo where `done`=0 and genre = %s and prg_freeendat > %s and prg_freeendat is not null  and prg_freeendat < %s order by prg_freeendat asc limit 1 ;",(genre,starttime,starttime + dynamic_day *24 * 60 * 60));

        i = cur.fetchone()
        if not i:
            continue
        cur.execute("update abemavideo set done=2 where prg_id = %s;",(i[0],)) #set working
        db.commit()
        # season title may null
        # replace '/' in folder names
        if i[3] :
            dirname = i[2].strip().encode('utf-8').replace("/","／")+"/"+ i[3].strip().encode('utf-8').replace("/","／")
        else:
            dirname = i[2].strip().encode('utf-8').replace("/","／")
        # / --> ／
        filename = i[1].strip().encode('utf-8').replace("/","／")
        stream = i[5] 
        if stream.endswith(".mpd") or stream is None:
            #mark -2 and continue
            pass
        # stream = "https://abema.tv/video/episode/{0}".format(i[0])
        ret = subprocess.call(["streamlink",stream,"best","--quiet","--http-headers","X-Forwarded-For={0}".format(random.choice(JAPANIPS)),"--hls-segment-threads","2","-o","./{0}.mp4".format(filename)])
        if ret!=0:
            print "error downloading {0}/{1} id:{2} and delete tmp file!!".format(dirname,filename,i[0])
            try:
                os.unlink("./{0}.mp4".format(filename))
            except Exception as e:
                print str(e)
            # cur.execute("update abemavideo set done=-2 where prg_id = %s;",(i[0],))
            # db.commit()                
            continue
        else:
            print "Download finished. Start uploading!"
            slptime = os.path.getsize("./{0}.mp4".format(filename))/1000/1000/4
        while True:
            ret2 = subprocess.call(["./deps/rclone/rclone","--config","./deps/rclone/abema.conf","--size-only","--tpslimit" ,"1","--retries-sleep","10m","copy","./{0}.mp4".format(filename),"abema_{0}:{1}".format(genre,dirname)])
            if ret2 == 0:
                break
            else:
                print "Retry uploading!!!!"
                time.sleep(5*60)
        os.unlink("./{0}.mp4".format(filename))
        cur.execute("update abemavideo set done=1 where prg_id = %s;",(i[0],))
        db.commit()
        print "Upload to abema_{0}:{1}/{2}".format(genre,dirname,filename)
        last = genre 
        time.sleep(slptime)
