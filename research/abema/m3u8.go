/*
Before build
> go get ./...
Build
> go build
CrossPlatform Build
> GOOS= GOARCH= go build

*/
package main

import (
	"bytes" //create request payload
	"crypto/aes"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/binary"
	"encoding/hex" // bin <-> hex
	"encoding/json"
	"flag" // arg parse
	"fmt"
	"github.com/golang/groupcache/lru"
	"github.com/satori/go.uuid"
	"io"        // copy from reader to writer
	"io/ioutil" // ReadAll resp body
	"log"
	"math"
	"math/big" //calc bigint
	"math/rand"
	"net" // parse IP cidr
	"net/http"
	"os" // for log os.Stderr
	"regexp"
	"strconv" // convert timestamp to string
	"strings" // find index in strtable
	"time"
)

/*
1.USING FAKE JAPAN_IP
2. PROXY STREAM
3. PROXY STREAM SIZE

*/

// for api v1/channels
type channelJson struct {
	Channels []struct {
		Id       string
		Name     string
		Playback struct {
			Hls  string
			Dash string
		}
	}
}

type slotJson struct {
	Slot struct {
		Flags struct {
			TimeshiftFree bool
		}
		Playback struct {
			Hls string
		}
	}
}

type episodeJson struct {
	Label struct {
		Free bool
	}
	Playback struct {
		Hls string
	}
}

//options
var USING_JAPAN_IP = flag.Bool("fakeip", true, "For those who aare not in Japan")
var PROXY_STREAM = flag.Bool("proxyts", true, "Proxy ts stream ")
var TS_SIZE = flag.Int("tssize", 128*1024, "Buffer size for proxied ts [only valid when proxy ts specified]")
var LISTEN_SERVER = flag.String("l", ":8888", "Listen IP:PORT")
var DETAILED_LOG = flag.Bool("v", false, "Detailed log")
var FORCE_RESOLUTION = flag.Int("f", 1080, "Force resolution [valid value: 180,240,360,480,720,1080,4096(experimental) ]")

func generate_japan_ip() string {
	ips := []string{"126.0.0.0/8", "133.0.0.0/8", "43.0.0.0/9", "153.128.0.0/9", "43.128.0.0/10", "60.64.0.0/10", "106.128.0.0/10", "180.0.0.0/10", "219.0.0.0/10", "220.0.0.0/10"}
	rand.Seed(time.Now().UnixNano())
	addr, subnet, _ := net.ParseCIDR(ips[rand.Intn(len(ips))])
	masksize, allsize := subnet.Mask.Size()
	count := uint32(math.Pow(2, float64(allsize-masksize)))
	test_count := 10
	res := make(chan string, 1)
	done := make(chan bool, test_count)
	for i := 0; i < test_count; i++ {
		go func(resip chan<- string, allsignal chan<- bool, val uint32) {
			testip := func(ip net.IP, v uint32) net.IP {
				tmpip := make(net.IP, 4)
				binary.BigEndian.PutUint32(tmpip, binary.BigEndian.Uint32(ip[12:16])+v)
				return tmpip
			}(addr, val)
			client := &http.Client{}
			req, _ := http.NewRequest("HEAD", "https://abematv.akamaized.net/region", nil)
			req.Header.Add("X-Forwarded-For", testip.String())
			resp, _ := client.Do(req)
			defer resp.Body.Close()
			if resp.StatusCode == http.StatusOK {
				resip <- testip.String()
			}
			allsignal <- true
		}(res, done, rand.Uint32()%count)
	}

	result, err := func() (string, error) {
		var inner_count int = 0
		for {
			select {
			case <-done:
				inner_count += 1
				if inner_count == test_count {
					return "", fmt.Errorf("No result")
				}
			case val := <-res:
				return val, nil
			}
		}

	}()
	if err != nil {
		//again
		return generate_japan_ip()
	}
	return result
}

func generate_applicationkeysecret(deviceid string) string {
	var SECRETKEY = []byte("v+Gjs=25Aw5erR!J8ZuvRrCx*rGswhB&qdHd_SYerEWdU&a?3DzN9BRbp5KwY4hEmcj5#fykMjJ=AuWz5GSMY-d@H7DMEh3M@9n2G552Us$$k9cD=3TxwWe86!x#Zyhe")
	var t = (time.Now().Unix() + 60*60) / 3600 * 3600
	var t_struct = time.Unix(t, 0).UTC()
	var t_str = strconv.FormatInt(t, 10)
	var mac = hmac.New(sha256.New, SECRETKEY)
	mac.Write(SECRETKEY)
	var tmp = mac.Sum(nil)
	for i := 0; i < int(t_struct.Month()); i++ {
		mac = hmac.New(sha256.New, SECRETKEY)
		mac.Write(tmp)
		tmp = mac.Sum(nil)
	}
	mac = hmac.New(sha256.New, SECRETKEY)
	mac.Write([]byte(base64.RawURLEncoding.EncodeToString(tmp) + deviceid))
	tmp = mac.Sum(nil)
	for i := 0; i < t_struct.Day()%5; i++ {
		mac = hmac.New(sha256.New, SECRETKEY)
		mac.Write(tmp)
		tmp = mac.Sum(nil)
	}
	mac = hmac.New(sha256.New, SECRETKEY)
	mac.Write([]byte(base64.RawURLEncoding.EncodeToString(tmp) + t_str))
	tmp = mac.Sum(nil)
	for i := 0; i < t_struct.Hour()%5; i++ {
		mac = hmac.New(sha256.New, SECRETKEY)
		mac.Write(tmp)
		tmp = mac.Sum(nil)
	}
	return base64.RawURLEncoding.EncodeToString(tmp)

}

func get_videokey_from_ticket(ticket string, deviceid string, usertoken string) []byte {
	client := &http.Client{}
	var params = "osName=android&appVersion=3.27.1&osTimezone=Asia%2FTokyo&osLang=ja_JP&appId=tv.abema&osVersion=6.0.1"
	req, _ := http.NewRequest("GET", "https://api.abema.io/v1/media/token"+"?"+params, nil)
	req.Header.Add("Authorization", "Bearer "+usertoken)
	resp, _ := client.Do(req)
	body, _ := ioutil.ReadAll(resp.Body)
	resp.Body.Close()
	var tmp map[string]string
	_ = json.Unmarshal(body, &tmp)
	var mediatoken = tmp["token"]
	json_data, _ := json.Marshal(map[string]string{"kv": "a", "lt": ticket})
	resp, _ = http.Post("https://license.abema.io/abematv-hls"+"?t="+mediatoken, "application/json", bytes.NewBuffer(json_data))
	body, _ = ioutil.ReadAll(resp.Body)
	resp.Body.Close()
	_ = json.Unmarshal(body, &tmp)
	var cid = tmp["cid"]
	var klen = len(tmp["k"])
	var k = []byte(tmp["k"])
	bigval := big.NewInt(0)
	const STRTABLE = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
	for i, v := range k {
		tmpval := new(big.Int)
		tmpval.Exp(big.NewInt(58), big.NewInt(int64(klen-1-i)), nil)
		tmpval.Mul(tmpval, big.NewInt(int64(strings.IndexByte(STRTABLE, v))))
		bigval.Add(bigval, tmpval)
	}
	encvideokey := bigval.Bytes()

	INITKEY, _ := hex.DecodeString("3AF0298C219469522A313570E8583005A642E73EDD58E3EA2FB7339D3DF1597E")
	mac := hmac.New(sha256.New, INITKEY)
	mac.Write([]byte(cid + deviceid))
	enckey := mac.Sum(nil)

	cipher, _ := aes.NewCipher(enckey)
	decrypted := make([]byte, len(encvideokey))
	size := cipher.BlockSize()
	for bs, be := 0, size; bs < len(encvideokey); bs, be = bs+size, be+size {
		cipher.Decrypt(decrypted[bs:be], encvideokey[bs:be])
	}
	return decrypted
}

func main() {
	// flag
	usage_old := flag.Usage
	flag.Usage = func() {
		usage_old()
		//detailed
		fmt.Fprintf(flag.CommandLine.Output(), "For those who are in Japan: --fakeip=no --proxyts=no is recomended\nFor those who are away from Japan: no args (defaults)  or --fakeip=yes --proxyts=yes is recommended\n\nOpen videoplayer and input : http://<ip:port>/  for a random channel or http://<ip:port>/now-on-air/abema-news for abema-news channel\n")
	}
	flag.Parse()

	//logger
	applog := log.New(os.Stderr, "", log.Ldate|log.Ltime|log.Lshortfile)
	applog.Println("Initializing!!!")

	var JAPAN_IP string
	if *USING_JAPAN_IP {
		applog.Println("Searching valid Japan IP!!")
		JAPAN_IP = generate_japan_ip()
	}
	applog.Println("Using Japan IP:", JAPAN_IP)

	flagset := make(map[string]bool)
	flag.Visit(func(f *flag.Flag) { flagset[f.Name] = true })

	if flagset["f"] {
		if (*FORCE_RESOLUTION != 180) && (*FORCE_RESOLUTION != 240) && (*FORCE_RESOLUTION != 360) && (*FORCE_RESOLUTION != 480) && (*FORCE_RESOLUTION != 720) && (*FORCE_RESOLUTION != 1080) && (*FORCE_RESOLUTION != 4096) {
			applog.Println("Wrong Resolution : ", *FORCE_RESOLUTION)
			applog.Println("Valid Resolution Value: 180 240 360 480 720 1080 4096")
			flagset["f"] = false
		} else {
			applog.Println("Using Resolution : ", *FORCE_RESOLUTION)
		}
	}

	// initialize
	LICENSE_CACHE := lru.New(2048) // make(map[string][]byte)

	deviceid := uuid.Must(uuid.NewV4()).String()
	appkeysecret := generate_applicationkeysecret(deviceid)
	json_data, _ := json.Marshal(map[string]string{"deviceId": deviceid, "applicationKeySecret": appkeysecret})
	resp, _ := http.Post("https://api.abema.io/v1/users", "application/json", bytes.NewBuffer(json_data))
	body, _ := ioutil.ReadAll(resp.Body)
	resp.Body.Close()
	var t map[string]string
	_ = json.Unmarshal(body, &t)
	var usertoken = t["token"]
	//
	resp, _ = http.Get("https://api.abema.io/v1/channels")
	body, _ = ioutil.ReadAll(resp.Body)
	resp.Body.Close()
	var channels channelJson
	_ = json.Unmarshal(body, &channels)

	// handlers
	ticket_regexp := regexp.MustCompile(`/abematv-license/(.*)`)
	http.HandleFunc("/abematv-license/", func(w http.ResponseWriter, r *http.Request) {
		if *DETAILED_LOG {
			applog.Println(r.URL.Path)
		}
		matchres := ticket_regexp.FindStringSubmatch(r.URL.Path)
		if matchres == nil {
			return
		}
		ticket := matchres[1]
		if license, ok := LICENSE_CACHE.Get(ticket); ok {
			w.Write(license.([]byte))
		} else {
			license := get_videokey_from_ticket(ticket, deviceid, usertoken)
			//LICENSE_CACHE[ticket] = license
			LICENSE_CACHE.Add(ticket, license)
			w.Write(license)
		}
	})

	// 0-> all 1-> program/channel/slot 2-> name  4->quality
	channel_regexp := regexp.MustCompile(`/(channel|program|slot)/(?P<name>[^\/^\.]*)(/(?P<quality>\d+))?/playlist\.m3u8`)
	change_license_regexp := regexp.MustCompile(`"(abematv-license)://(\w*)"`)
	ts_regexp := regexp.MustCompile(`/(.*?)(/.*\.ts(\?.*)?)`)
	change_relative_regxp := regexp.MustCompile(`https://(.*)-abematv\.akamaized\.net(.*)`) //include linear and vod
	//ts_regexp := regexp.MustCompile(`/.*\.ts$`)
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		if *DETAILED_LOG {
			applog.Println("in /" , r.URL.Path)
		}
		if matcheres := ts_regexp.FindStringSubmatch( r.URL.Path); matcheres != nil {
			applog.Println("In ts handling")
			d_type := matcheres[1]
			url := matcheres[2]
			w.Header().Set("Content-Type", "video/MP2T")
			client := &http.Client{}
			req, _ := http.NewRequest("GET", fmt.Sprintf("https://%s-abematv.akamaized.net%s",d_type,url), nil)
			if *USING_JAPAN_IP {
				req.Header.Add("X-Forwarded-For", JAPAN_IP)
			}
			resp, _ := client.Do(req)
			defer resp.Body.Close()
			buf := make([]byte, *TS_SIZE)
			io.CopyBuffer(w, resp.Body, buf)

		} else if matchres := channel_regexp.FindStringSubmatch(r.URL.Path) ; matchres!=nil{
			applog.Println("In m3u8 handling")
			client := &http.Client{}
			if matchres[4] == "" { 
				name := matchres[2]
				v_type := matchres[1]
				if flagset["f"] { // set resolution implictly
					http.Redirect(w, r, fmt.Sprintf("/%s/%s/%d/playlist.m3u8",v_type, name, *FORCE_RESOLUTION), http.StatusFound)
					return
				}
				var req_str string
				switch v_type {
				case "program":
					req_str = fmt.Sprintf("https://vod-abematv.akamaized.net/%s/%s/playlist.m3u8",v_type, name)
				case "slot":
					req_str = fmt.Sprintf("https://vod-abematv.akamaized.net/%s/%s/playlist.m3u8",v_type, name)
				case "channel":
					req_str = fmt.Sprintf("https://linear-abematv.akamaized.net/%s/%s/playlist.m3u8",v_type, name)
	
				}
				applog.Println("Req str",req_str)
				req, _ := http.NewRequest("GET", req_str, nil)
				if *USING_JAPAN_IP {
					req.Header.Add("X-Forwarded-For", JAPAN_IP)
				}
				w.Header().Set("Content-Type", "application/x-mpegURL")
				resp, _ := client.Do(req)
				defer resp.Body.Close()
				io.Copy(w, resp.Body)
				return
				//no quality
			} else {
				applog.Println("having quality!!!")
				name := matchres[2]
				v_type := matchres[1]
				quality := matchres[4]
				var req_str string
				switch v_type {
				case "program":
					req_str = fmt.Sprintf("https://vod-abematv.akamaized.net/%s/%s/%s/playlist.m3u8",v_type, name ,quality)
				case "slot":
					req_str = fmt.Sprintf("https://vod-abematv.akamaized.net/%s/%s/%s/playlist.m3u8",v_type, name, quality)
				case "channel":
					req_str = fmt.Sprintf("https://linear-abematv.akamaized.net/%s/%s/%s/playlist.m3u8",v_type, name, quality)
	
				}
				req, _ := http.NewRequest("GET", req_str, nil)
				if *USING_JAPAN_IP {
					req.Header.Add("X-Forwarded-For", JAPAN_IP)
				}
				w.Header().Set("Content-Type", "application/x-mpegURL")
				resp, _ := client.Do(req)
				defer resp.Body.Close()
				body, _ := ioutil.ReadAll(resp.Body)
				body = change_license_regexp.ReplaceAll(body, []byte(`"/$1/$2"`))
				if *PROXY_STREAM {
					body = change_relative_regxp.ReplaceAll(body, []byte(`/$1$2`)) // /linear|vod(/tsurl)
				}
				w.Write(body)
				//with quality
			}
		} else if r.URL.Path == "/" {
			rand.Seed(time.Now().UnixNano())
			pick := channels.Channels[rand.Intn(len(channels.Channels))]
			if *DETAILED_LOG {
				applog.Println("Random Channel:", pick.Id, pick.Name)
			}
			redirecturl := change_relative_regxp.ReplaceAllString(pick.Playback.Hls, `$2`)
			http.Redirect(w, r, redirecturl, http.StatusFound)
			return
		} else {
			applog.Println("nothing matches")
			return
		}
	})

	noa_regexp := regexp.MustCompile(`/now-on-air/([a-zA-Z0-9\-]*)`)
	http.HandleFunc("/now-on-air/", func(w http.ResponseWriter, r *http.Request) {
		if *DETAILED_LOG {
			applog.Println(r.URL.Path)
		}
		matchres := noa_regexp.FindStringSubmatch(r.URL.Path)
		if matchres == nil {
			return
		}
		http.Redirect(w, r, fmt.Sprintf("/channel/%s/playlist.m3u8", matchres[1]), http.StatusFound)
	})

	slot_regexp := regexp.MustCompile(`/channels/.+?/slots/(?P<slots>[^\?]+)`)
	//slot
	http.HandleFunc("/channels/", func(w http.ResponseWriter, r *http.Request) {
		if *DETAILED_LOG {
			applog.Println(r.URL.Path)
		}
		matchres := slot_regexp.FindStringSubmatch(r.URL.Path)
		if matchres == nil {
			return
		}
		client := &http.Client{}
		req, _ := http.NewRequest("GET", fmt.Sprintf("https://api.abema.io/v1/media/slots/%s", matchres[1]), nil)
		req.Header.Add("Authorization", "Bearer "+usertoken)
		resp, _ := client.Do(req)
		defer resp.Body.Close()
		if resp.StatusCode == http.StatusNotFound {
			w.WriteHeader(http.StatusNotFound)
			return
		}
		body, _ := ioutil.ReadAll(resp.Body)
		var slots slotJson
		_ = json.Unmarshal(body, &slots)
		if slots.Slot.Flags.TimeshiftFree == false {
			w.WriteHeader(http.StatusPaymentRequired)
			return
		}
		redirecturl := change_relative_regxp.ReplaceAllString(slots.Slot.Playback.Hls, `$2`)
		http.Redirect(w, r, redirecturl, http.StatusFound) //like slot/%s/playlist.m3u8"

	})
	episode_regexp := regexp.MustCompile(`/video/episode/(?P<episode>[^\?]+)`)
	http.HandleFunc("/video/episode/", func(w http.ResponseWriter, r *http.Request) {
		if *DETAILED_LOG {
			applog.Println(r.URL.Path)
		}
		matchres := episode_regexp.FindStringSubmatch(r.URL.Path)
		if matchres == nil {
			return
		}
		client := &http.Client{}
		req, _ := http.NewRequest("GET", fmt.Sprintf("https://api.abema.io/v1/video/programs/%s", matchres[1]), nil)
		req.Header.Add("Authorization", "Bearer "+usertoken)
		resp, _ = client.Do(req)
		defer resp.Body.Close()

		if resp.StatusCode == http.StatusNotFound {
			w.WriteHeader(http.StatusNotFound)
			return
		}
		body, _ = ioutil.ReadAll(resp.Body)
		var episode episodeJson
		_ = json.Unmarshal(body, &episode)
		if episode.Label.Free == false {
			w.WriteHeader(http.StatusPaymentRequired)
			return
		}
		redirecturl := change_relative_regxp.ReplaceAllString(episode.Playback.Hls, `$2`)
		applog.Println("ep hls",episode.Playback.Hls)
		http.Redirect(w, r, redirecturl, http.StatusFound) // like /program/%s/playlist.m3u8

	})

	applog.Println("Service started @", *LISTEN_SERVER, "!!!!!")
	applog.Fatal(http.ListenAndServe(*LISTEN_SERVER, nil))
	//fmt.Println(hex.EncodeToString(get_videokey_from_ticket("EYkgxWe4V3vNjoEGfvwA4Q",deviceid,usertoken)))
}
