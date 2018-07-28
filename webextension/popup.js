const pagePattern = /addPlayer\(\s*?'(?<player_id>.*?)',\s*?'(?<player_key>.*?)',\s*?'(?<catchup_id>.*?)',\s*?'(?<publisher_id>.*?)',\s*?'(?<reference_id>.*?)',\s*?'(?<title>.*?)',\s*?'(?<subtitle>.*?)',\s*?'(?<service>.*?)',\s*?'(?<servicename>.*?)',/gm;
const policyKeyPattern = /catalog\(\{accountId:\"?(?<accountId>.*?)\"?,policyKey:\"(?<policyKey>.*?)\"/gm;
const BCOV_POLICY = {
  //YTV
  "5330942432001":"BCpkADawqM0kGrWxZoXJvJj5Uv6Lypjp4Nrwzz1ktDAuEbD1r_pj0oR1900CRG04FFkxo0ikc1_KmAlB4uvq_GnFwF4IsG_v9jhYOMajC9MkdVQ-QrpboS7vFV8RvK20V5v-St5WGPfXotPx",
  //TX
  "3971130137001":"BCpkADawqM1F2YPxbuFJzWtohXjxdgDgIJcsnWacQKaAuaf0gyu8yxCQUlca9Dh7V0Uu_8Rt5JUWZTpgcqzD_IT5hRVde8JIR7r1UYR73ne8S9iLSroqTOA2P-jtl2EUw_OrSMAtenvuaXRF",
  //TBS
  "4031511847001":"BCpkADawqM1n_azNkrwm-kl2UhijTLt4W7KZ6KS9HluAoLPvyRFu2X4Xu2dUuW-lLOmc6X7WjsiBwh83m8ecNmxl-pVy9w3M9iI6-en-_wIDvNJixpoMf4BhdOPtwO_7XIol9P3wVrq2BIzw",
  "4394098881001":"BCpkADawqM3m-3484dphPL5raj3jQJVlFecOYAvpxhtJaK99BVRKtxd9SC6q0kOsknI1FD3kplVUaJzneAQb55EkCcDHrD9m_yoesmjsIfJpKQXJKfmQ5LfAFJnmf2Sv48heP_R1PGznwbAn",
  //NTV
  "4394098882001":"BCpkADawqM1s6XkqRoC2a0eEORY7FFF780eHkHQZ93Fw752A9swymrSMZEVF1d7G3mSby3Etzj8MGJp_ZwXpbSTH1ApfZxZ1FSPQ4LXDQhpaMRADtCbxKFTpAxGYwN61DYKKksmg4uwcdhLD",
  //MBS
  "5102072605001":"BCpkADawqM1VhDl0FtgrrM8jB-hVNkcrdrx4x9C_60OSeN4jIHynGkIKw0PY1cOsRqQYJOnJRscPAbdPTcpzZ_4g89Gcte_yQFW-yeWxzrPECulIh9ZlaZsJ_3rH7Gjs_RnuWHx_lTzilaxh",
  //KTV
  "5718741494001":"BCpkADawqM1llDtMelQ9nQyE91bAc-E5T1B0135MCCRZ_o4FlDkGWQY8t8Nrt1fJKAgui-kLefX-JGaRItrDXh_C1GlIgCSv-rhNPQYKJsY8nZp_IoJ38Mf3B5BSJLFulW0QhgQduipc9j4D",
  //EX no publisherid
 "4031511847001":"BCpkADawqM2N0e6IdrmQn-kEZJ0jRi-Dlm0aUZ9mVF2lcadunJzMVYD6j_51UZzQ3mXuIeV8Zx_UUvbGeeJn73SSrpm0xD7qtiKULPP2NEsp_rgKoVxVWTNZAHN-JAHcuIpFJT7PvUj6gpZv",
  //ABC   
  "5102072603001":"BCpkADawqM2NfzEA47jZiJNK0SYahFenNwAtoehfrIAaCqxmHjBidnt_YfvFnp5j-Zi58FPj-zXAHATYU1nnOOuEf9XXV8JRGYSuZ5dgyNc2RjGv2Ej5zGfhxWs3_p4F7huxtbAD9fzQlg7b",
  //World cup
  "5764318572001":"BCpkADawqM3KJLCLszoqY9KsoXN2Mz52LwKx4UXYRuEaUGr-o3JBSHmz_0WRicxowBj8vmbGRK_R7Us96DdBYuYEoVX9nHJ3DjkVW5-8L6bRmm6gck8IaeLLw21sM6mOHtNs9pIJPF6a4qSZlO6t_RlkpMY6sasaIaSYlarJ_8PFMPdxxfY6cGtJDnc"
}


chrome.tabs.executeScript({
  code: "var tmpdata = {href : window.location.href,page : document.children[0].innerHTML};tmpdata",
  runAt: "document_start"
}, function(results) {
  let href = results && results[0].href || '';
  let page = results && results[0].page || ''; // #RAIDO or http://m3u8list   
  if (/tver\.jp/.test(href)) {
    //parse
    let res;
    if ((res = pagePattern.exec(page)) == null) {
      return
    }
    if(res.groups.service == 'cx'){
      //TODO
      let infoapi = res.groups.publisher_id.length == 4 ? "https://i.fod.fujitv.co.jp/plus7/web/"+res.groups.publisher_id +".html" : "https://i.fod.fujitv.co.jp/plus7/web/"+res.groups.publisher_id.slice(0,4) +"/"+res.groups.publisher_id +".html" 
    }else{
      let title = res.groups.title;
      let subtitle = res.groups.subtitle;
      let player_id = res.groups.player_id;
      let reference_id = res.groups.service == 'tx' ? res.groups.reference_id : "ref:"+res.groups.reference_id;
      fetch("https://players.brightcove.net/"+ player_id +"/"+ res.groups.player_key +"_default/index.min.js")
      .then((resp) =>{ return resp.text();}).then(function(text){
        let mres,policyKey;
        if((mres = policyKeyPattern.exec(text)) == null){
          policyKey = BCOV_POLICY[player_id]
        }else{
          policyKey = mres.groups.policyKey
        }
        console.log(player_id,policyKey)
        fetch("https://edge.api.brightcove.com/playback/v1/accounts/" + player_id + "/videos/" + reference_id, {
            headers: {
              "X-Forwarded-For": "1.0.16.0",
              "Accept": "application/json;pk=" + policyKey
            }
          }).then(response => response.json()).then(function(json){
            let sources = json["sources"];
            let src = sources.filter(function(i){ return i["ext_x_version"] == 3 && i["src"].startsWith("http://")} )[0]["src"]
            document.write("streamlink "+src+" best --hls-segment-threads 10 -o "+title +"_"+ subtitle+ ".mp4" )

          })
        
      })

    }
  }

});