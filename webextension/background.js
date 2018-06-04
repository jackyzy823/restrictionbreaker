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

//for firefox 
// change response to -> 
// <RESULT>
// <FLAG TYPE="true"/>
// </RESULT>

// do not work under iframe?
chrome.webRequest.onBeforeSendHeaders.addListener(function(req){
  console.log("in fuji fod!!!")
  //block geocontrol1. for fod-geo
  //add cookie to domain i.fod....
  // let it retry itself
  
  // samesite --> from chrome51
  chrome.cookies.set({url:"https://i.fod.fujitv.co.jp/",domain:"i.fod.fujitv.co.jp",name:"geo",value:"true",httpOnly:false,expirationDate: Date.now()/1000.0+3600000},function(res){
  console.log(res);
  });//need fujitv.co.jp permission in manifest
  return {cancel:true};

},{urls:["*://geocontrol1.stream.ne.jp/fod-geo/check.xml*"]},["blocking"])
