import os
import subprocess
import time
import sqlite3
# from streamlink import Streamlink
# import streamlink
import json

db  =sqlite3.connect("db_tver.db",check_same_thread  =False)
cur = db.cursor()
cur.execute("select  `reference_id` , `service` , `player_id` , `name` , `title` , `subtitle` , `catchup_id` , `url` , `service_name` , `id` , `json` ,`rowid` from tver where `done`!=1 order by updated_at asc ;");
# from multiprocessing.dummy import Pool
res = cur.fetchall()
for i in res:
    if i[1]=='cx':
        stream = i[10]
    else:
        sources = json.loads(i[10])["sources"]
        for source in sources:
            if source["ext_x_version"] == "3" and source["src"].startswith("http://"):
                break
        stream = source["src"] 
    try:
        dirname = i[4].strip(u'\u3000').strip().encode("utf-8")
        # mkdir_p("./dst/{0}/{1}".format(i[1],dirname))
        filename = i[5].strip(u'\u3000').strip().encode("utf-8")
        if len(filename) == 0:
            filename = i[3].encode("utf-8").strip()
        ret = subprocess.call(["streamlink",stream,"best","--hls-segment-threads","3","-o","./{0}.mp4".format(filename)])
        if ret!=0:
            print "error downloading {0}".format(i[7])
            break
        else:
            print "Download finished. Start uploading!"
        while True:
            ret2 = subprocess.call(["./deps/rclone/rclone","--config","./deps/rclone/rclone.conf","--ignore-existing","--tpslimit" ,"1","copy","./{0}.mp4".format(filename),"tver:{0}/{1}".format(i[1],dirname)])
            if ret2 == 0:
                break
            else:
                print "Retry uploading!!!!"
                time.sleep(2*60+5)
        os.unlink("./{0}.mp4".format(filename))
        cur.execute("update  tver set done=1 where rowid = ?",(i[11],))
        db.commit()
    except Exception as e:
        print str(e)
        print "Failed! URL:{0}".format(i[7])
