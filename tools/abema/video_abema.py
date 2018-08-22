from abema import generateUserInfo
import requests
(userid,deviceid,usertoken) = generateUserInfo()

genres = requests.get("https://api.abema.io/v1/video/genres",headers = {"Authorization":"Bearer "+usertoken}).json()["genres"]
interested = ['variety','animation','drama','reality','documentary','movie', 'music']
for i in interested:
    cards = []
    while True:
        next_ = ''
        respj = requests.get("https://api.abema.io/v1/video/featureGenres/<genre>/cards?limit=20&next={0}&onlyFree=true".format(next_)).json()
        cards += respj["cards"]
        if respj['paging']['next'] == '':
            break
        else:
            next_ = respj['paging']['next']
    for item in cards:
        seriesId = item['seriesId']
        title = item['title']
        caption = item['caption']
        programProvidedInfo = item['programProvidedInfo']
        if len(programProvidedInfo.keys())!=0:
            print seriesId,title
        

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