import uuid
from datetime import datetime,timedelta
from base64 import urlsafe_b64encode
import time

import hmac
import hashlib

import requests
#Cipher

deviceId = str(uuid.uuid4())

def genTime():
    d = datetime.now()
    d = d.replace(year=2018,month=7,day=16,hour=16,minute=0,second=0,microsecond=0)
    d += timedelta(hours=1)
    return d

'''
                byte[] doFinal = instance.doFinal();
                for (i2 = 0; i2 < cQ.getMonthValue(); i2++) {
                    doFinal = instance.doFinal(doFinal);
                }
 byte[] bytes = (Base64.encodeToString(doFinal, 11) + str).getBytes(C.UTF8_NAME);
                    instance.reset();
                    instance.update(bytes);
                    doFinal = instance.doFinal();
                    for (i2 = 0; i2 < cQ.getDayOfMonth() % 5; i2++) {
                        doFinal = instance.doFinal(doFinal);
                    }
                        bytes = (Base64.encodeToString(doFinal, 11) + cQ.g(q.eCu)).getBytes(C.UTF8_NAME);
                        instance.reset();
                        instance.update(bytes);
                        bytes = instance.doFinal();
                        while (i < cQ.getHour() % 5) {
                            bytes = instance.doFinal(bytes);
                            i++;
                        }
                        return Base64.encodeToString(bytes, 11);


                '''
'''
date: Mon, 16 Jul 2018 08:07:56 GMT
applicationKeySecret
:
"2knbNxyXKDNHDy4Tab1nhEUueR5iEub-vt0uSovc5PA"
deviceId
:
"401551ae-086f-45e6-96b3-dfcc176982c7"

'''
#   NO_PADDING -> remove =
#   URLSAFE ->
def generateApplicationKeySecret(deviceId, timeinfo):
    h = hmac.new("v+Gjs=25Aw5erR!J8ZuvRrCx*rGswhB&qdHd_SYerEWdU&a?3DzN9BRbp5KwY4hEmcj5#fykMjJ=AuWz5GSMY-d@H7DMEh3M@9n2G552Us$$k9cD=3TxwWe86!x#Zyhe",digestmod=hashlib.sha256)
    h.update("v+Gjs=25Aw5erR!J8ZuvRrCx*rGswhB&qdHd_SYerEWdU&a?3DzN9BRbp5KwY4hEmcj5#fykMjJ=AuWz5GSMY-d@H7DMEh3M@9n2G552Us$$k9cD=3TxwWe86!x#Zyhe")
    tmp = h.digest()
    print tmp.encode('hex')
    for i in range(timeinfo.month):
        h = hmac.new("v+Gjs=25Aw5erR!J8ZuvRrCx*rGswhB&qdHd_SYerEWdU&a?3DzN9BRbp5KwY4hEmcj5#fykMjJ=AuWz5GSMY-d@H7DMEh3M@9n2G552Us$$k9cD=3TxwWe86!x#Zyhe",digestmod=hashlib.sha256)
        h.update(tmp)
        tmp = h.digest()
        print tmp.encode('hex')
    # step 2
    h = hmac.new("v+Gjs=25Aw5erR!J8ZuvRrCx*rGswhB&qdHd_SYerEWdU&a?3DzN9BRbp5KwY4hEmcj5#fykMjJ=AuWz5GSMY-d@H7DMEh3M@9n2G552Us$$k9cD=3TxwWe86!x#Zyhe",digestmod=hashlib.sha256)
    h.update(urlsafe_b64encode(tmp).replace("=","")+deviceId)
    tmp = h.digest()
    for i in range(timeinfo.day % 5):
        h = hmac.new("v+Gjs=25Aw5erR!J8ZuvRrCx*rGswhB&qdHd_SYerEWdU&a?3DzN9BRbp5KwY4hEmcj5#fykMjJ=AuWz5GSMY-d@H7DMEh3M@9n2G552Us$$k9cD=3TxwWe86!x#Zyhe",digestmod=hashlib.sha256)
        h.update(tmp)
        tmp = h.digest()
    #step 3
    print "before timestamp",tmp.encode('hex')
    h = hmac.new("v+Gjs=25Aw5erR!J8ZuvRrCx*rGswhB&qdHd_SYerEWdU&a?3DzN9BRbp5KwY4hEmcj5#fykMjJ=AuWz5GSMY-d@H7DMEh3M@9n2G552Us$$k9cD=3TxwWe86!x#Zyhe",digestmod=hashlib.sha256)
    print urlsafe_b64encode(tmp)+ str(int(time.mktime(timeinfo.timetuple())))
    h.update(urlsafe_b64encode(tmp).replace("=","")+ str(int(time.mktime(timeinfo.timetuple())))) # no .0 
    tmp = h.digest()
    print "before hour",tmp.encode('hex')

    for i in range(8 % 5): # should be utc hour!!!
        h = hmac.new("v+Gjs=25Aw5erR!J8ZuvRrCx*rGswhB&qdHd_SYerEWdU&a?3DzN9BRbp5KwY4hEmcj5#fykMjJ=AuWz5GSMY-d@H7DMEh3M@9n2G552Us$$k9cD=3TxwWe86!x#Zyhe",digestmod=hashlib.sha256) 
        h.update(tmp)
        tmp = h.digest()
    return urlsafe_b64encode(tmp)

generateApplicationKeySecret("401551ae-086f-45e6-96b3-dfcc176982c7",genTime())



# requests.post("https://api.abema.io/v1/users",data={"deviceId":deviceId,"applicationKeySecret":})
'''
refernece java base64 from  https://android.googlesource.com/platform/frameworks/base/+/master/core/java/android/util/Base64.java
import java.io.UnsupportedEncodingException;
import java.security.InvalidKeyException;
import java.security.Key;
import java.security.NoSuchAlgorithmException;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

//java 8
import java.time.LocalDateTime;
import java.time.ZoneOffset; 
import java.time.temporal.ChronoUnit; 

import javax.xml.bind.DatatypeConverter;


public class Test {
    public static String a(String str, LocalDateTime fVar) {
        Throwable e;
        int i = 0;
        LocalDateTime cQ = fVar.plusHours(1); //+1hour
        try {
            Key secretKeySpec = new SecretKeySpec("v+Gjs=25Aw5erR!J8ZuvRrCx*rGswhB&qdHd_SYerEWdU&a?3DzN9BRbp5KwY4hEmcj5#fykMjJ=AuWz5GSMY-d@H7DMEh3M@9n2G552Us$$k9cD=3TxwWe86!x#Zyhe".getBytes("utf-8"), "HmacSHA256");
            Mac instance = Mac.getInstance("HmacSHA256");
            instance.init(secretKeySpec);
            try {
                int i2;
                instance.update("v+Gjs=25Aw5erR!J8ZuvRrCx*rGswhB&qdHd_SYerEWdU&a?3DzN9BRbp5KwY4hEmcj5#fykMjJ=AuWz5GSMY-d@H7DMEh3M@9n2G552Us$$k9cD=3TxwWe86!x#Zyhe".getBytes("utf-8"));
                byte[] doFinal = instance.doFinal();
                System.out.printf("Step1:%s\n",DatatypeConverter.printHexBinary(doFinal));
                for (i2 = 0; i2 < cQ.getMonthValue(); i2++) {
                    doFinal = instance.doFinal(doFinal);
                    System.out.printf("Dofinal:%s\n",DatatypeConverter.printHexBinary(doFinal));
                }
                System.out.printf("month:%d\n",cQ.getMonthValue());
                try {
                    System.out.printf("Step1:%s\n",DatatypeConverter.printHexBinary(doFinal));
                    byte[] bytes = (Base64.encodeToString(doFinal, 11) + str).getBytes("utf-8");
                    instance.reset();
                    instance.update(bytes);
                    doFinal = instance.doFinal();
                    for (i2 = 0; i2 < cQ.getDayOfMonth() % 5; i2++) {
                        doFinal = instance.doFinal(doFinal);
                    }
                    try {
                        bytes = (Base64.encodeToString(doFinal, 11) + cQ.toEpochSecond(ZoneOffset.UTC)).getBytes("utf-8");
                        instance.reset();
                        instance.update(bytes);
                        bytes = instance.doFinal();
                        while (i < cQ.getHour() % 5) {
                            bytes = instance.doFinal(bytes);
                            i++;
                        }
                        return Base64.encodeToString(bytes, 11);
                    } catch (Throwable e2) {
                        System.out.println("error");
                            return null;
                    }
                } catch (Throwable e22) {
                                            System.out.println("error");

                        return null;
                }
            } catch (Throwable e222) {
                        System.out.println("error");

                    return null;
            }
        } catch (UnsupportedEncodingException e3) {
                        System.out.println("error");

                return null;
        } catch (InvalidKeyException e4) {
                        System.out.println("error");

                return null;
        } catch (NoSuchAlgorithmException e5) {
                        System.out.println("error");

                return null;
        }
    }

    public static void main(String[] args) {
        LocalDateTime dt = LocalDateTime.of(2018, 7, 16, 8, 00); 
        System.out.println(a("uuid",dt));
    }
}

'''