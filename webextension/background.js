const CHOSENIP = getRandomIp();
console.log("Your IP:"+CHOSENIP+",You can change it by reload the extension if some site blocks this IP.");


chrome.webRequest.onBeforeSendHeaders.addListener(function(req){
  console.log("why firefox do not go into here? "+req.url);
  req.requestHeaders = req.requestHeaders.filter(function(x){
    return x.name.toLowerCase()!= 'x-forwarded-for';
  });
  req.requestHeaders.push({name:'X-Forwarded-For',value:CHOSENIP})//TODO:random japan ip
  return {
    requestHeaders:req.requestHeaders
  }
},
{urls:["*://*.dmm.co.jp/*","*://*.api.brightcove.com/playback/*","*://abematv.akamaized.net/region*","*://linear-abematv.akamaized.net/*","*://vod-abematv.akamaized.net/*"]},["blocking","requestHeaders"])
/*
DMM preview does not work http://www.dmm.co.jp/service/-/html5_player/=/cid= /mtype=AhRVShI_/service=digital/floor=videoa/mode=/
http://www.dmm.co.jp/service/newrecommend/-/recommends_call/ does not work
*/
if(chrome.webRequest.filterResponseData){
  chrome.webRequest.onBeforeRequest.addListener(function(req){
    let filter = chrome.webRequest.filterResponseData(req.requestId);
    let respJson = null;
    filter.onstart = function(event){
        console.log("rewrite on!!!");
    }
    filter.ondata = function(event){
      //save data
      if(respJson == null){
        respJson = event.data;
      }
      else{
        respJson += event.data;
      }
      // do not pass through
    }
    filter.onstop = function(event){
      let encoder = new TextEncoder();
      let decoder = new TextDecoder();
      let r = JSON.parse(decoder.decode(respJson));//String.fromCharCode.apply(null, new Uint8Array(respJson))
      r.cue_points=[];
      filter.write(encoder.encode(JSON.stringify(r)));
      //write modified to
      filter.disconnect();
    }        
  },{urls:["*://*.api.brightcove.com/playback/*"]},["blocking"]);
}
else{
  chrome.webRequest.onBeforeRequest.addListener(function(req){
    return {redirectUrl: 'data:text/xml,<?xml version="1.0"?> <vmap:VMAP xmlns:vmap="http://www.iab.net/videosuite/vmap" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:a="http://www.auditude.com/schema" version="1.0"> </vmap:VMAP>'}
    // return {cancel:true}
  },{urls:["*://ad.auditude.com/adserver/vmap1*"]},["blocking"])
  // inspect and monkey patch xhr? https://www.moesif.com/blog/technical/apirequest/How-We-Captured-AJAX-Requests-with-a-Chrome-Extension/
  ////does not work because it needs resposeheaders for statistics ,but redirecturl cannot provide
  // const BCOV_POLICY = {
  //   //YTV
  //   "5330942432001":"BCpkADawqM0kGrWxZoXJvJj5Uv6Lypjp4Nrwzz1ktDAuEbD1r_pj0oR1900CRG04FFkxo0ikc1_KmAlB4uvq_GnFwF4IsG_v9jhYOMajC9MkdVQ-QrpboS7vFV8RvK20V5v-St5WGPfXotPx",
  //   //TX
  //   "3971130137001":"BCpkADawqM1F2YPxbuFJzWtohXjxdgDgIJcsnWacQKaAuaf0gyu8yxCQUlca9Dh7V0Uu_8Rt5JUWZTpgcqzD_IT5hRVde8JIR7r1UYR73ne8S9iLSroqTOA2P-jtl2EUw_OrSMAtenvuaXRF",
  //   //TBS
  //   "4031511847001":"BCpkADawqM1n_azNkrwm-kl2UhijTLt4W7KZ6KS9HluAoLPvyRFu2X4Xu2dUuW-lLOmc6X7WjsiBwh83m8ecNmxl-pVy9w3M9iI6-en-_wIDvNJixpoMf4BhdOPtwO_7XIol9P3wVrq2BIzw",
  //   "4394098881001":"BCpkADawqM3m-3484dphPL5raj3jQJVlFecOYAvpxhtJaK99BVRKtxd9SC6q0kOsknI1FD3kplVUaJzneAQb55EkCcDHrD9m_yoesmjsIfJpKQXJKfmQ5LfAFJnmf2Sv48heP_R1PGznwbAn",
  //   //NTV
  //   "4394098882001":"BCpkADawqM1s6XkqRoC2a0eEORY7FFF780eHkHQZ93Fw752A9swymrSMZEVF1d7G3mSby3Etzj8MGJp_ZwXpbSTH1ApfZxZ1FSPQ4LXDQhpaMRADtCbxKFTpAxGYwN61DYKKksmg4uwcdhLD",
  //   //MBS
  //   "5102072605001":"BCpkADawqM1VhDl0FtgrrM8jB-hVNkcrdrx4x9C_60OSeN4jIHynGkIKw0PY1cOsRqQYJOnJRscPAbdPTcpzZ_4g89Gcte_yQFW-yeWxzrPECulIh9ZlaZsJ_3rH7Gjs_RnuWHx_lTzilaxh",
  //   //KTV
  //   "5718741494001":"BCpkADawqM1llDtMelQ9nQyE91bAc-E5T1B0135MCCRZ_o4FlDkGWQY8t8Nrt1fJKAgui-kLefX-JGaRItrDXh_C1GlIgCSv-rhNPQYKJsY8nZp_IoJ38Mf3B5BSJLFulW0QhgQduipc9j4D",
  //   //EX no publisherid
  //   //ABC   
  //   "5102072603001":"BCpkADawqM2NfzEA47jZiJNK0SYahFenNwAtoehfrIAaCqxmHjBidnt_YfvFnp5j-Zi58FPj-zXAHATYU1nnOOuEf9XXV8JRGYSuZ5dgyNc2RjGv2Ej5zGfhxWs3_p4F7huxtbAD9fzQlg7b",
  //   //World cup
  //   "5764318572001":"BCpkADawqM3KJLCLszoqY9KsoXN2Mz52LwKx4UXYRuEaUGr-o3JBSHmz_0WRicxowBj8vmbGRK_R7Us96DdBYuYEoVX9nHJ3DjkVW5-8L6bRmm6gck8IaeLLw21sM6mOHtNs9pIJPF6a4qSZlO6t_RlkpMY6sasaIaSYlarJ_8PFMPdxxfY6cGtJDnc"
  // }
  // chrome.webRequest.onBeforeRequest.addListener(function(req){
  //   let publisherid = /accounts\/(\d*?)\/videos/.exec(req.url)[1];
  //   let policykey = BCOV_POLICY[publisherid];
  //   let myReq = new XMLHttpRequest();
  //   myReq.open('GET',req.url,false); 
  //   myReq.setRequestHeader('X-Forwarded-For',CHOSENIP);
  //   myReq.setRequestHeader("Accept","application/json;pk="+policykey);
  //   myReq.send();
  //   let json = myReq.response;
  //   json.cue_points = [];
  //   return {redirectUrl: "data:text/json;"+JSON.stringify(json)};

  // },{urls:["*://*.api.brightcove.com/playback/*"]},["blocking"]);
  //onbeforerequest -> redirect to xhr response (with x-forwarded-for and accept policy [get policy from publisherid]) the modify json
}


//OPTIONS for data url do not allow Access-Control-Request-Headers: x-requested-with
//preview
chrome.webRequest.onBeforeRequest.addListener(function(req){
  //not always correct
  //example: wanz00768 -> service tkwanz768 -> wanz00768
  let cid = /cid=(.*?)\//.exec(req.url)[1];
  if(cid.substr(-5,2) == "00"){
    cid = cid.substr(0,cid.length-5)+ cid.slice(-3);
  }
  //quality 300 -> sm 1000 -> dm 1500 -> dmb
  let videoUrl = "http://cc3001.dmm.co.jp/litevideo/freepv/"+cid[0]+"/"+cid.substr(0,3)+"/"+cid+"/"+cid+"_dmb_w.mp4";
  //chrome do not allow autoplay with sound.
  //TODO: resolve iframe cross-domain problem to allow closePlayer
  // seems impossible :https://blog.mozilla.org/security/2017/10/04/treating-data-urls-unique-origins-firefox-57/
  // except intercept this http://www.dmm.co.jp/digital/videoa/-/detail/ajax-movie/=/cid to avoid iframe? -> failed with XHR OPTIONS can not work correctly
  return {redirectUrl: "data:text/html,<video src=\""+videoUrl+"\" controls=\"controls\" width=\"100%\" height=\"100%\" preload onended=\"window.parent.closePlayer();\">"}
},{urls:["*://www.dmm.co.jp/service/-/html5_player/*"]},["blocking"])


// has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
// FAILED BECAUSE OF CORS (OPTIONS) what if req.method ==get ? (failed too)
//may do this via javascript ?
// see AbemaTVChromeExtension/xhr-injection.js . they custom xhr to change resolution
// chrome.webRequest.onBeforeRequest.addListener(function(req){
//   if(req.method.toLowerCase()=='get'){
//     console.log("force replace!!!!")
//     return {redirectUrl:req.url.replace(/\/\d+\/playlist.m3u8/,'/1080/playlist.m3u8')}
//   }
// },{urls:["*://linear-abematv.akamaized.net/channel/*/*/playlist.m3u8*"]},["blocking"])
/*
Abema resolution
https://linear-abematv.akamaized.net/channel/anime-live/720/playlist.m3u8
180 -> 1080
key use protocol abema-license:// 

*/


chrome.webRequest.onBeforeRequest.addListener(function(req){
  return {cancel:true}
},{urls:["http://www.tv-asahi.co.jp/douga/common/js/checkWithin.js"]},["blocking"])
// asahi can also redirect  within_area_check.php to dataurl


//for firefox 
// change response to -> 
// <RESULT>
// <FLAG TYPE="true"/>
// </RESULT>

// cookie may set after 3 times retry. may force to cancel slowly?
// new solution use redirect to data url
// double ensurence! 
chrome.webRequest.onBeforeRequest.addListener(function(req){
  chrome.cookies.set({url:"https://i.fod.fujitv.co.jp/",domain:"i.fod.fujitv.co.jp",name:"geo",value:"true",httpOnly:false,expirationDate: Date.now()/1000.0+3600000},function(res){
  });//need fujitv.co.jp permission in manifest
  return {redirectUrl: "data:text/xml,<RESULT> <FLAG TYPE=\"true\"/> </RESULT>"};
},{urls:["*://geocontrol1.stream.ne.jp/fod-geo/check.xml*"]},["blocking"])


//TODO: for FOD and firefox , ua -> chrome to avoid flash