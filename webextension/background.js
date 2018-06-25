chrome.webRequest.onBeforeSendHeaders.addListener(function(req){
  req.requestHeaders = req.requestHeaders.filter(function(x){
    return x.name.toLowerCase()!= 'x-forwarded-for';
  });
  req.requestHeaders.push({name:'X-Forwarded-For',value:'1.0.16.0'})//TODO:random japan ip
  return {
    requestHeaders:req.requestHeaders
  }
},
{urls:["*://*.api.brightcove.com/playback/*","*://abematv.akamaized.net/region*","*://linear-abematv.akamaized.net/*"]},["blocking","requestHeaders"])

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