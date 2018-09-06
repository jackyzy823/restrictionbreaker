from multiprocessing.dummy import Pool
from time import sleep
from itertools import product
import random
import socket

def get_url_worker(url,ip,chars):
    req_template =  'HEAD {0} HTTP/1.1\r\nHost:fod-plus7.hls.wseod.stream.ne.jp\r\n\r\n'.format(url)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, 80))
    for val in product("0123456789abcdef",repeat=2):
        while True:
            try:
                s.sendall(req_template%(chars[0],chars[1],val[0],val[1]))
                data = s.recv(1024)
                if data[9:12] != '404' and data[9:12] == '200':
                    s.close()
                    return url%(chars[0],chars[1],val[0],val[1])
                elif data[9:12] != '404':
                    if len(data) == 0:
                        time.sleep(1)
                    else:
                        print("stauscode: %s, at :%s  ->%s%s%s%s "%(data[9:12],ip,chars[0],chars[1],val[0],val[1]))
                        break
                else:
                    break
            except socket.error:
                s.close()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((ip, 80))
    s.close()
    return False

def get_url(vid):
    ips = [ "52.85.219.%d"%(i) for i in range(1,129)]+["52.85.218.%d"%(i) for i in range(1,129)]
    random.shuffle(ips)
    p = Pool(16*16)
    get_url.res = None
    first_chr = vid[0]
    series = vid[:4]
    if first_chr in '01234':
        padding = '01234'
    elif first_chr in '56789':
        padding = '56789'
    else:
        padding = 'abcedf'

    url_template = '/www08/fod-plus7/_definst_/mp4:video/{0}/{1}/{2}me113%s%s%s%s.mp4/playlist.m3u8'.format(padding,series,vid)

    def get(x):
        # nonlocal res
        if x:
            get_url.res = x
            p.terminate()
    for i in zip(ips,product("0123456789abcdef",repeat=2)):
        p.apply_async(get_url_worker,(url_template,i[0],i[1]),callback = get)
    p.close()
    p.join()
    return get_url.res



if __name__ == '__main__':
    import sys
    # get_url_worker('/www08/fod-plus7/_definst_/mp4:video/01234/4c07/4c07810009me113%s%s%s%s.mp4/playlist.m3u8',"52.85.219.1",("1","2"))
    print(get_url(sys.argv[1]))
