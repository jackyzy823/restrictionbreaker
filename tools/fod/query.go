package main

import (
	"fmt"
	"net/http"
	"os"
	"io"
	"io/ioutil"
)

//"https://fod-plus7.hls.wseod.stream.ne.jp/www08/fod-plus7/_definst_/mp4:video/01234/4f50/4f50810001me113%c%c%c%c.mp4/playlist.m3u8"
func main() {
	str_table := "0123456789abcdef"
	template := os.Args[1]
	res := make(chan string, 1)
	done := make(chan bool, 65536)
	for i := 0; i < 16; i++ {
		for j := 0; j < 16; j++ {
			go func(resUrl chan<- string, allsignal chan<- bool, v_i int, v_j int) {
				for k := 0; k < 16; k++ {
					for l := 0; l < 16; l++ {
						url := fmt.Sprintf(template, str_table[v_i], str_table[v_j], str_table[k], str_table[l])
						resp, err := http.Head(url)
						if resp != nil {
							defer resp.Body.Close()
						}
						if err != nil {
							l -= 1
							// fmt.Println(err)
						} else {
							_, _ = io.Copy(ioutil.Discard, resp.Body)
							if resp.StatusCode != http.StatusNotFound && resp.StatusCode == http.StatusOK {
								resUrl <- url
							}
							allsignal <- true
						}
					}
				}
				
			}(res, done, i, j)
		}
	}

	result, _ := func() (string, error) {
		var inner_count int = 0
		for {
			select {
			case <-done:
				inner_count += 1
				os.Stdout.Write([]byte(fmt.Sprintf("\r%05d/65536 -> %4.2f%%",inner_count, float64(inner_count) / 655.36)))
				if inner_count == 65536 {
					return "", fmt.Errorf("No result")
				}
			case val := <-res:
				return val, nil
			}
		}

	}()
	fmt.Println("\nres", result)
}
