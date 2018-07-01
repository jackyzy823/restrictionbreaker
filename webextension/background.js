const CHOSENIP = getRandomIp();
console.log("Your IP:"+CHOSENIP+",You can change it by reload the extension if some site blocks this IP.");


chrome.webRequest.onBeforeSendHeaders.addListener(function(req){
  console.log("why firefox do not go into here?")
  req.requestHeaders = req.requestHeaders.filter(function(x){
    return x.name.toLowerCase()!= 'x-forwarded-for';
  });
  req.requestHeaders.push({name:'X-Forwarded-For',value:CHOSENIP})//TODO:random japan ip
  return {
    requestHeaders:req.requestHeaders
  }
},
{urls:["*://*.dmm.co.jp/*","*://*.api.brightcove.com/playback/*","*://abematv.akamaized.net/region*","*://linear-abematv.akamaized.net/*"]},["blocking","requestHeaders"])
/*
DMM preview does not work http://www.dmm.co.jp/service/-/html5_player/=/cid= /mtype=AhRVShI_/service=digital/floor=videoa/mode=/
http://www.dmm.co.jp/service/newrecommend/-/recommends_call/ does not work
*/

//preview
chrome.webRequest.onBeforeRequest.addListener(function(req){
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


/*
<iframe type="text/html" src="http://www.dmm.co.jp/service/-/html5_player/=/cid=1star788/mtype=AhRVShI_/service=digital/floor=videoa/mode=/" id="DMMSample_player_now" width="560" height="440" scrolling="no" border="0" style="border:none;" frameborder="0" allowfullscreen="" allow="autoplay"></iframe>
*/

//force 1080
chrome.webRequest.onBeforeRequest.addListener(function(req){

  return {redirectUrl:req.url.replace(/\/\d+\/playlist.m3u8/,'/1080/playlist.m3u8')}

},{urls:["*://linear-abematv.akamaized.net/channel/*/playlist.m3u8"]},["blocking"])
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