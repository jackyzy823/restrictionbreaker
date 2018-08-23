from abema import generateUserInfo
import requests
(userid,deviceid,usertoken) = generateUserInfo()
s = requests.session()
s.headers.update({"Authorization":"Bearer "+usertoken ,"User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",})

genres = s.get("https://api.abema.io/v1/video/genres",headers = {"Authorization":"Bearer "+usertoken}).json()["genres"]
interested = ['variety']#,'animation','drama','reality','documentary','movie', 'music']
for genre in interested:
    cards = []
    next_ = ''
    while True:
        respj = s.get("https://api.abema.io/v1/video/featureGenres/{0}/cards?limit=20&next={1}&onlyFree=true".format(genre,next_)).json()
        cards += respj["cards"]
        print respj['paging']
        if respj['paging'].get("next","") == '':
            break
        else:
            next_ = respj['paging']['next']
            print next_
    # print cards
    for item in cards:

        seriesId = item['seriesId']
        title = item['title']
        caption = item.get('caption','')
        if item["label"].get("someFree"):
            freetype = "someFree"
        elif item["label"].get("free"):
            freetype = "free"

        print seriesId,title,caption,freetype
        programProvidedInfo = item['programProvidedInfo']
        if len(programProvidedInfo.keys())!=0:
            print "Having providedInfo",seriesId,title
        resp = s.get("https://api.abema.io/v1/video/series/{0}".format(seriesId)).json()
        print resp
        break

        

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