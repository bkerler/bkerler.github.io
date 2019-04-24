#!/usr/bin/env python3
import os
import sys
from struct import unpack

filename=sys.argv[1]
filesize=os.stat(filename).st_size

def seekforpartitions(rf):
    pos=0
    partitions=[]
    while(pos<filesize):
        rf.seek(pos)
        data=rf.read(0x20004)
        idx=data.find(b"\xC3\xCA\x00\x00")
        if idx!=-1:
            rf.seek(pos+idx+0x90)
            namedata=rf.read(0x20)
            ridx=namedata.find(b"\x00")
            namedata=namedata[:ridx]
            if (ridx!=-1) and len(namedata)>3 and namedata!="" and namedata.isalpha():
                found=False
                for partition in partitions:
                    if namedata.decode('utf-8') in partition["name"]:
                        found=True
                if not found:
                    partitions.append(dict(name=namedata.decode('utf-8'),start=pos+idx,end=0))
                    print(f"Detected partition {namedata.decode('utf-8')} at {hex(pos+idx)}")
        pos+=0x20000
    return partitions

with open(filename,'rb') as rf:
    partitions=seekforpartitions(rf)

    for i in range(0,len(partitions)-1):
        partitions[i]["end"]=partitions[i+1]["start"]
    partitions[len(partitions)-1]["end"]=filesize

    for partition in partitions:
        start=partition["start"]
        end=partition["end"]
        rf.seek(start)
        offset=rf.tell()
        partname=partition["name"]+".bin"
        print(f"Writing {partname}")
        blk_sz=4096
        with open(partname,"wb") as wf:
            while (offset<end):
                header_bin = rf.read(12)
                header = unpack("<2H2I", header_bin)
                chunk_type = header[0]
                chunk_sz = header[2]
                total_sz = header[3]
                data_sz = total_sz - 12
                if chunk_type == 0xCAC1:
                    if data_sz != (chunk_sz * blk_sz):
                        print("Raw chunk input size (%u) does not match output size (%u)"
                              % (data_sz, chunk_sz * blk_sz))
                        break
                    else:
                        curtype = "Raw data"
                        data = rf.read(chunk_sz * blk_sz)
                        wf.write(data)
                elif chunk_type == 0xCAC2:
                    if data_sz != 4:
                        print("Fill chunk should have 4 bytes of fill, but this has %u"
                              % (data_sz))
                        break
                    else:
                        fill_bin = rf.read(4)
                        fill = unpack("<I", fill_bin)
                        curtype = format("Fill with 0x%08X" % (fill))
                        data = fill_bin * (blk_sz / 4);
                        wf.write(data)
                elif chunk_type == 0xCAC3:
                    wf.write(b'\x00' * chunk_sz * blk_sz)
                elif chunk_type == 0xCAC4:
                    if data_sz != 4:
                        print("CRC32 chunk should have 4 bytes of CRC, but this has %u"
                              % (data_sz))
                        break
                    else:
                        crc_bin = rf.read(4)
                        crc = unpack("<I", crc_bin)
                        curtype = format("Unverified CRC32 0x%08X" % (crc))
                else:
                    print("Unknown chunk type 0x%04X" % (chunk_type))
                    break
                offset += chunk_sz
    print("Done.")