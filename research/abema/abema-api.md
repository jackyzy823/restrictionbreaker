1.User Generate

REQ: POST https://api.abema.io/v1/users

DATA 
```json
{
    "deviceId": "UUID",
    "applicationKeySecret": "<generated by devideId and time>"
}
```
RESP:

DATA
```json
{
    "profile": {
        "userId": "",
        "createdAt": "UNIX timestamp"
    },
    "token": "userToken(JWT type)"
}
```

NOTE:

if deviceId is duplicated ,response an error. 409 
```json
{
    "message": "rpc error: code = AlreadyExists desc = service: device already registered = deviceId"
}
```

token is userToken which is a JWT . decode the second part -> 
```json
{
    "dev": "deviceId",
    "exp": "<UNIX TIMESTAMP +20years?>",
    "iss": "abema.io/v1",
    "sub": "userId"
}
```

2.OneTimePassword (Transfer step 1)

REQ: PUT https://api.abema.io/v1/users/<userid>/oneTimePassword

HEADER: Authorization: Bearer userToken

DATA 
```json
{"password":""}
```

3.OneTimePassword Auth (Transfer step 2 , in tmpdeviceId,tmpuserToken and tmpuserId)

REQ POST https://api.abema.io/v1/auth/oneTimePassword

HEADER Authorization: Bearer tmpuserToken

DATA
```json
{"userId":"","password":""}
```
RESP
```json
{"profile": {"userId":"","createdAt": time } , "token":"newuserToken" ,"subscriptions":[]}
```

so tmpuserId ,tmpuserToken is dropped,but  tmpdeviceId remians.
decode the newuserToken second part  -> deviceId is tmpdeviceId

so we can  know that a userId can link to multi deviceId ,and userToke is related to userId AND deviceId

4.MediaToken

PC version:

REQ GET https://api.abema.io/v1/media/token

PARAMS osName pc osVersion 1.0.0 osLang ja_JP osTimezone Asia/Tokyo appVersion v6.0.2 (from app.js)

HEADER Authorization: Bearer userToken

RESP
```json
{"token": "mediatoken"}
```

ANDROID VERSION

REQ `GET https://api.abema.io/v1/media/token`

PARAMS `osName android osVersion 6.0.1(android version) osLang ja_JP osTimezone Asia/Tokyo appId tv.abema appVersion 3.27.1(app version)`

HEADER Authorization: Bearer userToken

RESP
```json
{"token": "mediatoken"}
```

NOTE: generate mediatoken for user

5.M3U8 license (aka: ticket)

Note: ticket is related to video/channel ,has no relationship with user'id,device,token

REQ GET playlist.m3u8

RESP

abematv-license://<ticket>








