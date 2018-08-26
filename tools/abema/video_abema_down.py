import os
import os.path
import subprocess
import time
import sqlite3
import random
import netaddr

JAPANIPS = netaddr.IPNetwork('43.0.0.0/9')

'''
done = 0  not started
done = 1 finished
done = -1 expired!
done = -2 unchecked error
'''
db  =sqlite3.connect("db_abemavideo.db",check_same_thread  =False)
cur = db.cursor()
last = None
while True:
    starttime = int(time.time())
    cur.execute("select count(*) from abemavideo where done = 0 and prg_freeendat > ? and prg_freeendat is not null;",(starttime,))
    cnt = cur.fetchone()[0];
    if cnt == 0:
        break
    for genre in ('reality','animation','drama','variety','documentary','movie', 'music'):
        if genre == last:
            print "Only this site!!!!"
            time.sleep(60) #same site
        cur.execute("select  `prg_id` , `prg_title` , `series_title` , `season_title` , `prg_freeendat`  , `prg_url` ,  `rowid` from abemavideo where `done`==0 and genre = ? and prg_freeendat > ? and prg_freeendat is not null order by prg_freeendat asc ;",(genre,starttime,));

        i = cur.fetchone()
        if not i:
            continue

        # season title may null
        # replace '/' in folder names
        if i[3] :
            dirname = i[2].strip().replace("/","_")+"/"+ i[3].strip().replace("/","_")
        else:
            dirname = i[2].strip().replace("/","_")
        dirname = dirname.encode('utf-8')
        filename = i[1].strip().replace("/","_").encode('utf-8')
        stream = i[5] 
        # stream = "https://abema.tv/video/episode/{0}".format(i[0])
        ret = subprocess.call(["streamlink",stream,"best","--quiet","--http-headers","X-Forwarded-For={0}".format(random.choice(JAPANIPS)),"--hls-segment-threads","2","-o","./{0}.mp4".format(filename)])
        if ret!=0:
            print "error downloading {0}/{1} id:{2} and delete tmp file!!".format(dirname,filename,i[0])
            try:
                os.unlink("./{0}.mp4".format(filename))
            except Exception as e:
                print str(e)
            # cur.execute("update abemavideo set done=-2 where rowid = ?",(i[6],))
            # db.commit()                
            continue
        else:
            print "Download finished. Start uploading!"
            slptime = os.path.getsize("./{0}.mp4".format(filename))/1000/1000/4
        while True:
            ret2 = subprocess.call(["./deps/rclone/rclone","--config","./deps/rclone/abema.conf","--ignore-existing","--tpslimit" ,"1","copy","./{0}.mp4".format(filename),
                                    "abema_{0}:{1}".format(genre,dirname)])
            if ret2 == 0:
                break
            else:
                print "Retry uploading!!!!"
                time.sleep(2*60+5)
        os.unlink("./{0}.mp4".format(filename))
        cur.execute("update abemavideo set done=1 where rowid = ?",(i[6],))
        db.commit()
        print "Upload to abema_{0}:{1}/{2}".format(genre,dirname,filename)
        last = genre 
        time.sleep(slptime)
