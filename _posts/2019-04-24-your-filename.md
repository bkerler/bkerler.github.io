---
published: false
---
## Reversing an Oppo ozip encryption key

A friendly and warm welcome to the start of my reversing blog in memory of Fravia's ORC.

In this lesson, we are choosing a rather easy target before we're heading the more advanced targets such as Qualcomm Basebands. For today, we will concentrate on how to reverse engineer
an aes encryption key for those nifty encrypted oppo firmware packages with ".ozip" extension.

We will use Ghidra for reversing, so if you haven't installed it yet, take your time and grab your copy at [https://ghidra-sre.org](here) or for automated install on ubuntu/debian, use my installer over [https://github.com/bkerler/ghidra_installer](here).

As a start, in order to understand what we need, take a look at my repo implementing the ozip [https://github.com/bkerler/oppo_ozip_decrypt/blob/master/ozipdecrypt.py](decrypter) in python 3.x. Basically you can see that the encrypted ozip files always start with an header "OPPOENCRYPT!" at the first 12 bytes. The data to be decrypted starts at the offset 0x1050 and
is usually encrypted using a simple aes 128 with mode ECB and a block size of 0x4000 bytes.

In order to test if our key is valid, we just take the first 16 bytes and try to decrypt it with our reversed 16 bytes key using the aes_dec function. If the key is the right one, we should see a regular zip header "PK..." or bytes "504B0304" in the hex editor after decryption.

So, in order to understand where those ozip files are decrypted, there are usually two types of suspects where we can
search for. The first one, is the "/sbin/recovery" from the recovery in case your device is rooted. If it's not rooted however, I highly recommend the "/vendor/lib64/libapplypatch_jni.so" instead which is the easiest one to get. So, enable the adb debugging on your target device, then run 

```
~> adb pull /vendor/lib64/libapplypatch_jni.so
```

Once you got it, fire up ghidra. Our example target will be the RMX1831EX_11.A.07 ozip, available [https://www.realme.com/in/support/software-update#](here), MD5:4F4F7ABAF4993726576CD7FCBA89B43D.

