chrome.webRequest.onBeforeSendHeaders.addListener(function(req){
  console.log("im working!!!!!!!!!!!!")
  req.requestHeaders = req.requestHeaders.filter(function(x){
    return x.name.toLowerCase()!= 'x-forwarded-for';
  });
  req.requestHeaders.push({name:'X-Forwarded-For',value:'1.0.16.0'})//TODO:random japan ip
  return {
    requestHeaders:req.requestHeaders
  }
},
{urls:["*://*.api.brightcove.com/playback/*","*://abematv.akamaized.net/region*","*://linear-abematv.akamaized.net/*"]},["blocking","requestHeaders"])

