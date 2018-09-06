import os
import subprocess
import time
import json


'''
done = 0  not started
done = 1 finished
done = -1 expired!
done = -2 unchecked error
'''
# import sqlite3
# db  =sqlite3.connect("db_tver.db",check_same_thread  =False)
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
except mysql.connector.Error,ex:
    sys.exit(err.errno)
cur = db.cursor(buffered=True)


last = None
while True:
    cur.execute("select count(*) from tver where done = 0;");
    cnt = cur.fetchone()[0]
    if cnt == 0:
        cur.execute("select count(*) from tver where done = -2;");
        cnt = cur.fetchone()[0]
        print "Error status count:{0}".format(cnt)
        break
    for svc in ("tbs","tx", "ex", "ntv", "cx", "ktv", "mbs", "abc", "ytv"):
        if svc == last:
            print "Only this site!!!!"
            time.sleep(60) #same site
        cur.execute("select  `reference_id` , `service` , `player_id` , `name` , `title` , `subtitle` , `catchup_id` , `url` , `service_name` , `id` , `json` ,`rowid` from tver where `done` = 0 and service = %s order by updated_at asc ;",(svc,));
        i = cur.fetchone()
        if not i:
            continue

        if svc=='cx':
            stream = i[10]
        else:
            sources = json.loads(i[10])["sources"]
            for source in sources:
                if source["ext_x_version"] == "3" and source["src"].startswith("http://"):
                    break
            stream = source["src"]
        try:
            dirname = i[4].strip(u'\u3000').strip().encode("utf-8")
            filename = i[5].strip(u'\u3000').strip().encode("utf-8") #subtitle
            if len(filename) == 0:
                filename = i[3].encode("utf-8").strip() #name

            ret = subprocess.call(["streamlink",stream,"best","--quiet","--hls-segment-threads","1","-o","./{0}.mp4".format(filename)])
            if ret!=0:
                print "error downloading {0} and delete tmp file!!".format(i[7])
                try:
                    os.unlink("./{0}.mp4".format(filename))
                except Exception as e:
                    print str(e)
                    pass
                cur.execute("update  tver set done=-2 where rowid = %s;",(i[11],))
                db.commit()                
                continue
            else:
                print "Download finished. Start uploading!"
            while True:
                ret2 = subprocess.call(["./deps/rclone/rclone","--config","./deps/rclone/rclone.conf","--ignore-existing","--tpslimit" ,"1","copy","./{0}.mp4".format(filename),"{0}:{1}".format(svc,dirname)])
                if ret2 == 0:
                    break
                else:
                    print "Retry uploading!!!!"
                    time.sleep(2*60+5)
            os.unlink("./{0}.mp4".format(filename))
            cur.execute("update  tver set done=1 where rowid = %s;",(i[11],))
            db.commit()
            print "Upload to {0}:{1}/{2}".format(svc,dirname,filename)
        except Exception as e:
            print str(e)
            print "Failed! URL:{0}".format(i[7])
        last = svc