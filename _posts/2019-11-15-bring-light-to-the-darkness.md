---
layout:     post
title:      Reversing a Qualcomm Hexagon QDSP modem for profit
date:       2019-11-15 11:00:00
summary:    How to reverse engineer a modem backdoor
categories: reversing
thumbnail: jekyll
tags:
 - firmware
---

## Bring light to the darkness - Reversing a Qualcomm Hexagon QDSP modem for profit

A friendly and warm welcome to the first part of my Qualcomm reversing and exploitation blog in memory of Fravia's ORC and frequently requested by my twitter followers. This research wouldn't have been possible without the great people at 4PDA but also for Zibri who
first pointed me to the sierra wireless modem (and its engineering stuff) more than 10 years ago.

The modem we are reverse engineering today is the em7655 modem used in many devices, such as Laptops, Netgear Wifi Routers etc.
In the past, the such called "AT!OPENLOCK" functionality, which enables some secret engineering functionality was easy to reverse engineer as the old Qualcomm basebands (MDM7xxx) were used to have a simple ARM baseband. But things tend to change and Qualcomm went for a QDSP processor called Hexagon. With at first no tools available, the task of reverse engineering seemed hard. But then, tools appeared in the darkness. After some people contacted me being suppressed by their provider (or government, who knows), asking for a solution for the newer Netgear Routers (MR1100), I decided to have a look at the current generation and thus at the latest Hexagon technology.

However, even now having access to several tools such as Radare and the IDA GSMK or Hexagoon plugin, things turned out to be harder than expected. At first I simply reverse engineered the new algorithm used by Sierra Wireless but it seems that even with reversing and emulating the hexagon processor, the algorithm didn't work. Thus I had to dig deeper to figure out what might be causing my algorithm to fail.

But first things first, let's first show you how to reverse engineer a Qualcomm QDSP modem, having nothing else than a simple firmware blob.

Seeking for a modem which uses the em7655 module, the first google result seems to be the Dell Wireless 5806, which is in fact a rebranded em7655 module.

So let's simply download the firmware over [here](https://drive.google.com/drive/folders/1-SnjxoYjI69G6rsCaHGIkD8uDsOYmjSa).

After downloading, we need to unpack the firmware as we won't install the binary.
```bash
bjk@none:~/em7655$ unzip 291RY_A00_Build3724_Setup_ZPE.exe 
Archive:  291RY_A00_Build3724_Setup_ZPE.exe
  inflating: Configuration.ini       
  inflating: Setup.exe               
  inflating: Version.txt  
```

```bash
bjk@none:~/em7655$ 7z x Setup.exe
7-Zip [64] 16.02 : Copyright (c) 1999-2016 Igor Pavlov : 2016-05-21
p7zip Version 16.02 (locale=en_US.UTF-8,Utf16=on,HugeFiles=on,64 bits,8 CPUs Intel(R) Core(TM) i7-6700K CPU @ 4.00GHz (506E3),ASM,AES-NI)

Scanning the drive for archives:
1 file, 139734418 bytes (134 MiB)

Extracting archive: Setup.exe
--       
Path = Setup.exe
Type = Nsis
Physical Size = 139734418
Method = Deflate
Solid = -
Headers Size = 296264
Embedded Stub Size = 129536
SubType = NSIS-Park-1 Unicode log
```

```bash
bjk@none:~/em7655$ find -name *.cwe
./Images/5000/Generic/1/SWI9X15C_01.05.11.01.cwe
./Images/5000/Generic/6/SWI9X15C_01.05.11.03.cwe
./Images/5000/Generic/2/SWI9X15C_01.05.11.00.cwe
./Images/5000/Generic/3/SWI9X15C_01.05.11.02.cwe
```

The cwe files are the actual firmware we are interested in. So let's unpack the newest one.

```bash
bjk@none:~/em7655$ cd Images/5000/Generic/6
```
```bash
bjk@none:~/em7655/Images/5000/Generic/6$ wget https://downloads.sierrawireless.com/tools/swicwe/swicwe_latest.deb -O /tmp/swicwe_latest.deb
bjk@none:~/em7655/Images/5000/Generic/6$ sudo apt-get install /tmp/swicwe_latest.deb
```

```bash
bjk@none:~/em7655/Images/5000/Generic/6$ swicwe -@ SWI9X15C_01.05.11.03.cwe 
Image to split is SPKG, separating components...
output file name generated for QRPM component is BOOT9X15-QRPM9X15-SWI9X15C_01.05.11.03.cwe
Found QRPM component
output file name generated for SBL2 component is BOOT9X15-SBL29X15-SWI9X15C_01.05.11.03.cwe
Found SBL2 component
output file name generated for DSP1 component is MODM9X15-DSP19X15-SWI9X15C_01.05.11.03.cwe
Found DSP1 component
output file name generated for DSP2 component is MODM9X15-DSP29X15-SWI9X15C_01.05.11.03.cwe
Found DSP2 component
output file name generated for APBL component is APPL9X15-APBL9X15-SWI9X15C_01.05.11.03.cwe
Found APBL component
output file name generated for SYST component is APPL9X15-SYST9X15-SWI9X15C_01.05.11.03.cwe
Found SYST component
output file name generated for USER component is APPL9X15-USER9X15-SWI9X15C_01.05.11.03.cwe
Found USER component
output file name generated for APPS component is APPL9X15-APPS9X15-SWI9X15C_01.05.11.03.cwe
Found APPS component
```

As we guess that all AT commands are being handled by the DSP, let's have a look it this one...

```bash
bjk@none:~/em7655/Images/5000/Generic/6$ cd SWI9X15C_01.05.11.03.cwe-level-2-components/

bjk@none:~/em7655/Images/5000/Generic/6/SWI9X15C_01.05.11.03.cwe-level-2-components$ ls
APPL9X15-APBL9X15-SWI9X15C_01.05.11.03.cwe  BOOT9X15-QRPM9X15-SWI9X15C_01.05.11.03.cwe
APPL9X15-APPS9X15-SWI9X15C_01.05.11.03.cwe  BOOT9X15-SBL29X15-SWI9X15C_01.05.11.03.cwe
APPL9X15-SYST9X15-SWI9X15C_01.05.11.03.cwe  MODM9X15-DSP19X15-SWI9X15C_01.05.11.03.cwe
APPL9X15-USER9X15-SWI9X15C_01.05.11.03.cwe  MODM9X15-DSP29X15-SWI9X15C_01.05.11.03.cwe
```

```bash
bjk@none:~/em7655/Images/5000/Generic/6/SWI9X15C_01.05.11.03.cwe-level-2-components$ binwalk -e MODM9X15-DSP19X15-SWI9X15C_01.05.11.03.cwe
bjk@none:~/em7655/Images/5000/Generic/6/SWI9X15C_01.05.11.03.cwe-level-2-components$ binwalk -e MODM9X15-DSP29X15-SWI9X15C_01.05.11.03.cwe
```

As the DSP2 binary seems to have the at commands, but misses obviously the elf header, we just copy it from the dspv1 binary.

```bash
bjk@none:~/em7655/Images/5000/Generic/6/SWI9X15C_01.05.11.03.cwe-level-2-components$ dd if=_MODM9X15-DSP19X15-SWI9X15C_01.05.11.03.cwe.extracted/190 bs=1 count=52 of=~/em7655/modem.elf
52+0 records in
52+0 records out
52 bytes copied, 0,00120222 s, 43,3 kB/s

bjk@none:~/em7655/Images/5000/Generic/6/SWI9X15C_01.05.11.03.cwe-level-2-components$ cat _MODM9X15-DSP29X15-SWI9X15C_01.05.11.03.cwe.extracted/190 >> ~/em7655/modem.elf
```

In order to analyse the Hexagon Binary, let's first fire up IDA. For that, we will need a disassembler for hexagon DSP.
Sorry folks, there isn't yet any usable one for ghidra.

The most "usable" turned out to be the plugin made by a well known hacker @itsme over [here](https://github.com/gsmk/hexagon).

We will grep the .so Library for Linux [here](https://github.com/gsmk/hexagon/releases/download/v1.2/hexagon.so) and install it to the "procs" directory of IDA.
 
Fire up IDA32, open the "modem.elf" we created and select "Qualcomm Hexagon DSP v4" from the Processor type:

![IDA Hexagon]({{ site.baseurl }}/images/ida_hexagon.png "")

But wth is this ...

![IDA Error]({{ site.baseurl }}/images/ida_error.png "")

So we need to fix the elf header first. Using the 010 Editor and the elf template, fixing is easy.
We fix the e_entry_START_ADDRESS to be 0x41800000 (Using value from program table 2, Virtual Address)
and the value of program_table_element10, which seems to cause the ida error, to match the value
ida displayed (313868). Save it, and retry opening it up in IDA. So here we are.

![ELF Fix]({{ site.baseurl }}/images/elf_fix.png "")

It will take quite some time to analyse the modem elf, so take your time.

Now we search for "!OPENLOCK" using "Alt-B", make sure you use quotation marks for searching : 

![IDA Binary Search]({{ site.baseurl }}/images/ida_hexagon2.png "")

At the search result, in our case at @0x43347EB8, press "a" to get the ascii representation. It should then show
"!OPENLOCK". And having a look at the offset @0x43347EE5 we see a function pointer for that at command,
so we just press "o" at this offset.

We ain't got time to fully reverse the usage of each and every key, so we fit in the keys into the keys section of our python3 script [decrypter](https://github.com/bkerler/oppo_ozip_decrypt/blob/master/ozipdecrypt.py), and try to decrypt an ozip file for this device.

```bash
bjk@Lappy:~/Projects/oppo_ozip_decrypt$ ./ozipdecrypt.py RMX1831EX_11_OTA_0070_all_UqwwgT6ye4J1.ozip 
ozipdecrypt 0.3 (c) B.Kerler 2017-2019
Found correct AES key: acaa1e12a71431ce4a1b21bba1c1c6a2
Decrypting...
DONE!!
```

So it seems that the "userkey" is obviously the aes key needed to decrypt the oppo ozip files.

Mission accomplished :)

Stay tuned for following posts ....

