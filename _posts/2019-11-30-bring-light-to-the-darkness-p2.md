
## Bring light to the darkness - Reversing a Qualcomm Hexagon QDSP modem for profit - Part 2

Welcome back to the part 2 of my series on Qualcomm modem reversing and exploitation.

As we finished with reversing the main function of our interest, the function openlock_cmd @0xC24368C0
which is referred at the pointer table @0xC2435A90, let have a small primer on hexagon to get you started.

### Little how-to reverse hexagon 

Basically, instructions for different processors are usually almost the same. However, as the hexagon processor
is a QDSP, things are a bit different.

The qualcomm hexagon QDSP processor has 4 slots that can be run in parallel. This is the most important part to know,
so instructions aren't run each by another as you might be used to for most other platforms. The 4 slots are being used
in so called instruction packets that are marked with a start "{" and an end "}". Each instruction packet can contain up 
to four instructions (slots).

Both Slot 1 and Slot 2 can execute Load (LD), Store (ST), Arithmetic/Logical/32Bit (ALU32), whereas Slot 0 
is the only slot able to access Memory Operation (MEMOP), Cache/Bus/Prefetch (SYSTEM) and new-value (NV) instructions.

Slot 2 and Slot 3 can both execute extended type (XTYPE), ALU32 and jump (J) instructions, whereas only Slot 2 is able 
to execute Jump/Call register (JR) and Slot 3 only is able to execute control-register transfer (CR) instructions.

General registers are R0-R31 32-bit each, but there are control registers as well of course, such as the program counter (PC), 
and registers for loops (loop0/loop1). Also 64Bit and floating operations are possible.

You may also see some "immext" fields, which are immediate extensions. These "instructions" actually are just dwords that are 
being used by the following instruction to extend register values which given value may be to short and need to be 
extended, which is typical used for memory offsets.

The memb/memub/memh/memuh/memw/memd instructions are being used to load and store registers to/from memory, whereas
b stands for byte, ub for unsigned bytes, h for halfword, uh for unsigned halfword, d for dword.

If you see "GP", that stands for global pointer and is being used just like any global register, but it is being used 
for relative addressing.

Each instruction can make usage of predicate or general registers that are declared before the instruction packet 
(as we are used to) but also !within! the same instruction packet (which is then marked by .new after the register, 
also called new-value).

Let me show you a small code snippet that might explain that concept a bit clearer as it's very important :

### Instruction packets and its .new opcodes

We are going to calculate a simple value : 1 + 2 = 3 and we are going to store the byte value of it to a memory array at r3.

Here's the pseudo code :

```
r1=0
r1=r1+1
r1=r1+2
*r3=(byte) r1
```
 
Let's have a look at its hexagon disassembly:

```
1: { r1 = #0                #set r1 to 0
     r1 = add(r1, #1) }     #increase r1 by 1 (r1=1)

2: { r1 = add(r1, #2)       #increase r1 by 2 (r1=3)
     memb(r3+#0) = r1.new } #store register value that was modified in the current packet to r3 (*r3=r1)
```

The first byte value at the array of r3 now has a value of 3.

But now we are going to save r1 without the .new register instead :

```
1: { r1 = #0               #set r1 to 0
     r1 = add(r1, #1) }    #increase r1 by 1 (r1=1)

2: { r1 = add(r1, #2)      #increase r1 by 2 (r1=3)
     memb(r3+#0) = r1 }    #store register value from instruction packet 1 to r3 (*r3=r1)
```

The first byte value at the array of r3 now has a value of 1. That is because due to the missing .new opcode changes 
to r1 within the current instruction packet are ignored, but instead the value of r1 from the last instruction packet is being used.

That would correspond to this pseudo code instead:

```
r1=0
r1=r1+1
tmp_r1=r1+2
*r3=(byte) r1
```

### Let's have a look at some issues with current disassemblers

So when I started reverse engineering the AT!OPENLOCK algorithm, I tried to reconstruct the algorithm, however obvious issues
appeared. Let me show you some examples :

- IDA PRO 7.4 with GSMK Hexagon plugin

```
LOAD:C0BA003C                 { r3 = memub (gp + #0x1060)
LOAD:C0BA0040                   r4 = memub (r17 ++ #1) }
LOAD:C0BA0044                 { r5 = add (r3, #1)
LOAD:C0BA0048                   memb (gp + #0x1060) = r6.new } << There is no r6 in this packet ?!?
LOAD:C0BA004C                 { r5 = and (r5, #0xFF)
LOAD:C0BA0050                   r6 = memub (gp + #0x1061)
LOAD:C0BA0054                   r3 = memub (r2 + r3 << #0) }
LOAD:C0BA0058                 { r3 = add (r6, r3)
LOAD:C0BA005C                   r7 = add (r2, r5)
LOAD:C0BA0060                   memb (gp + #0x1061) = r4.new } << There is no r4 in this packet ?!?
LOAD:C0BA0064                 { r3 = and (r3, #0xFF)
LOAD:C0BA0068                   r0 = memub (gp + #0x105F)
LOAD:C0BA006C                   r14 = memub (gp + #0x105E) }
LOAD:C0BA0070                 { r12 = add (r2, r0)
LOAD:C0BA0074                   r13 = add (r2, r3)
LOAD:C0BA0078                   r8 = memub (r2 + r0 << #0)
LOAD:C0BA007C                   r9 = memub (r2 + r3 << #0) }
LOAD:C0BA0080                 { r28 = add (r2, r14)
LOAD:C0BA0084                   r15 = memub (gp + #0x1062)
LOAD:C0BA0088                   memb (r12 + #0) = r9 }
LOAD:C0BA008C                 { r18 = memub (r2 + r14 << #0)
LOAD:C0BA0090                   memb (r13 + #0) = r18.new }
LOAD:C0BA0094                 { r5 = memub (r2 + r5 << #0)
LOAD:C0BA0098                   memb (r28 + #0) = r6.new } << There is no r6 in this packet ?!?
LOAD:C0BA009C                 { memb (r7 + #0) = r8 }
LOAD:C0BA00A0                 { r1 = memub (r2 + r8 << #0) }
LOAD:C0BA00A4                 { r5 = add (r15, r1)
LOAD:C0BA00A8                   memb (gp + #0x1062) = r6.new } << There is no r6 in this packet ?!?
LOAD:C0BA00AC                 { r5 = and (r5, #0xFF)
LOAD:C0BA00B0                   r3 = memub (r2 + r3 << #0)
LOAD:C0BA00B4                   memb (gp + #0x105F) = r4 }
LOAD:C0BA00B8                 { r3 = add (r3, r8)
LOAD:C0BA00BC                   r6 = memub (r2 + r0 << #0)
LOAD:C0BA00C0                   r7 = memub (r2 + r14 << #0) }
LOAD:C0BA00C4                 { r3 = and (r3, #0xFF)
LOAD:C0BA00C8                   r5 = memub (r2 + r5 << #0) }
LOAD:C0BA00CC                 { r5 += add (r6, r7)
LOAD:C0BA00D0                   r3 = memub (r2 + r3 << #0) }
LOAD:C0BA00D4                 { r5 = and (r5, #0xFF)
LOAD:C0BA00D8                   r3 = xor (r3, r4) }
LOAD:C0BA00DC                 { r5 = memub (r2 + r5 << #0) }
LOAD:C0BA00E0                 { r5 = memub (r2 + r5 << #0) }
LOAD:C0BA00E4                 { r3 = xor (r3, r5)
LOAD:C0BA00E8                   memb (gp + #0x105E) = r4.new }      << There is no r4 in this packet ?!?
```

- Radare2 4.1.0-git 23209 @ linux-x86-64 git.4.0.0-138-g521ac7c28:

```
0xc0ba003c      034c2849       R3 = memub (gp + 0x1060)           << Ok, where are the instruction packets ?????
0xc0ba0040      24c0319b       R4 = memub (R17 ++ 1)
0xc0ba0044      254003b0       R5 = add (R3, 1)
0xc0ba0048      60c2a848       memb (gp + 0x1060) = R2            << R2 is an array, this doesn't make any sense
0xc0ba004c      e55f0576       R5 = and (R5, 255)
0xc0ba0050      264c2849       R6 = memub (gp + 0x1061)
0xc0ba0054      03c3223a       R3 = memub (R2 + R3 << 0x0)
0xc0ba0058      034306f3       R3 = add (R6, R3)
0xc0ba005c      074502f3       R7 = add (R2, R5)
0xc0ba0060      61c4a848       memb (gp + 0x1061) = R4            << Should be r4.new, or not ?
0xc0ba0064      e35f0376       R3 = and (R3, 255)
0xc0ba0068      e04b2849       R0 = memub (gp + 0x105f)
0xc0ba006c      cecb2849       R14 = memub (gp + 0x105e)
0xc0ba0070      0c4002f3       R12 = add (R2, R0)
0xc0ba0074      0d4302f3       R13 = add (R2, R3)
0xc0ba0078      0840223a       R8 = memub (R2 + R0 << 0x0)
0xc0ba007c      09c3223a       R9 = memub (R2 + R3 << 0x0)
0xc0ba0080      1c4e02f3       R28 = add (R2, R14)
0xc0ba0084      4f4c2849       R15 = memub (gp + 0x1062)
0xc0ba0088      00c90ca1       memb (R12 + 0) = R9
0xc0ba008c      124e223a       R18 = memub (R2 + R14 << 0x0)
0xc0ba0090      00c2ada1       memb (R13 + 0) = R2                << Again R2 is an array, doesn't make any sense
0xc0ba0094      0545223a       R5 = memub (R2 + R5 << 0x0)
0xc0ba0098      00c2bca1       memb (R28 + 0) = R2
0xc0ba009c      00c807a1       memb (R7 + 0) = R8
0xc0ba00a0      01c8223a       R1 = memub (R2 + R8 << 0x0)
0xc0ba00a4      05410ff3       R5 = add (R15, R1)
0xc0ba00a8      62c2a848       memb (gp + 0x1062) = R2
0xc0ba00ac      e55f0576       R5 = and (R5, 255)
0xc0ba00b0      0343223a       R3 = memub (R2 + R3 << 0x0)
0xc0ba00b4      5fc40848       memb (gp + 0x105f) = R4
0xc0ba00b8      034803f3       R3 = add (R3, R8)
0xc0ba00bc      0640223a       R6 = memub (R2 + R0 << 0x0)
0xc0ba00c0      07ce223a       R7 = memub (R2 + R14 << 0x0)
0xc0ba00c4      e35f0376       R3 = and (R3, 255)
0xc0ba00c8      05c5223a       R5 = memub (R2 + R5 << 0x0)
0xc0ba00cc      254706ef       R5 += add (R6, R7)
0xc0ba00d0      03c3223a       R3 = memub (R2 + R3 << 0x0)
0xc0ba00d4      e55f0576       R5 = and (R5, 255)
0xc0ba00d8      03c463f1       R3 = xor (R3, R4)
0xc0ba00dc      05c5223a       R5 = memub (R2 + R5 << 0x0)
0xc0ba00e0      05c5223a       R5 = memub (R2 + R5 << 0x0)
0xc0ba00e4      034563f1       R3 = xor (R3, R5)
0xc0ba00e8      5ec2a848       memb (gp + 0x105e) = R2          << Here we go again ... R2 is an array, doesn't make any sense
```

I had similar issues when I tried to use the hexagon objdump and back then, I couldn't figure out what the exact problem was.
There were other issues as well, like wrong registers being transferred and offset calculations.

From my past experience reporting bugs (and waiting months to be fixed) and trying to understand existing code and fix it myself (I didn't know how deep the rabbit hole in fact was) .... I decided to go through the pain and make a PoC disassembler for Hexagon V67 in Python, hoping at some point I would make usage of my code for creating a ghidra plugin, to make an emulator and to understand the hexagon architecture a bit better.

So here's the result :

```bash
~ ./hexagon_disasm.py modem.elf 0xc0ba003c 0xc0ba00e8

Hexagon V67 disassembler PoC (c) B.Kerler 2019

0xc0ba003c  {   034c2849        R3=memub(gp+#0x1060)    
0xc0ba0040      24c0319b        R4=memub(R17++#0x1)     }
0xc0ba0044  {   254003b0        R5=add(R3,#0x1) 
0xc0ba0048      60c2a848        memb(gp+#0x1060)=R5.new     }
0xc0ba004c  {   e55f0576        R5=and(R5,#0xff)    
0xc0ba0050      264c2849        R6=memub(gp+#0x1061)    
0xc0ba0054      03c3223a        R3=memub(R2+R3<<#0x0)       }
0xc0ba0058  {   034306f3        R3=add(R6,R3)   
0xc0ba005c      074502f3        R7=add(R2,R5)   
0xc0ba0060      61c4a848        memb(gp+#0x1061)=R3.new     }   < R3.new totally makes sense
0xc0ba0064  {   e35f0376        R3=and(R3,#0xff)    
0xc0ba0068      e04b2849        R0=memub(gp+#0x105f)    
0xc0ba006c      cecb2849        R14=memub(gp+#0x105e)       }
0xc0ba0070  {   0c4002f3        R12=add(R2,R0)  
0xc0ba0074      0d4302f3        R13=add(R2,R3)  
0xc0ba0078      0840223a        R8=memub(R2+R0<<#0x0)   
0xc0ba007c      09c3223a        R9=memub(R2+R3<<#0x0)       }
0xc0ba0080  {   1c4e02f3        R28=add(R2,R14) 
0xc0ba0084      4f4c2849        R15=memub(gp+#0x1062)   
0xc0ba0088      00c90ca1        memb(R12+#0x0)=R9       }
0xc0ba008c  {   124e223a        R18=memub(R2+R14<<#0x0) 
0xc0ba0090      00c2ada1        memb(R13+#0x0)=R18.new      }   < R18.new totally makes sense
0xc0ba0094  {   0545223a        R5=memub(R2+R5<<#0x0)   
0xc0ba0098      00c2bca1        memb(R28+#0x0)=R5.new       }
0xc0ba009c  {   00c807a1        memb(R7+#0x0)=R8        }
0xc0ba00a0  {   01c8223a        R1=memub(R2+R8<<#0x0)       }
0xc0ba00a4  {   05410ff3        R5=add(R15,R1)  
0xc0ba00a8      62c2a848        memb(gp+#0x1062)=R5.new     }
0xc0ba00ac  {   e55f0576        R5=and(R5,#0xff)    
0xc0ba00b0      0343223a        R3=memub(R2+R3<<#0x0)   
0xc0ba00b4      5fc40848        memb(gp+#0x105f)=R4     }
0xc0ba00b8  {   034803f3        R3=add(R3,R8)   
0xc0ba00bc      0640223a        R6=memub(R2+R0<<#0x0)   
0xc0ba00c0      07ce223a        R7=memub(R2+R14<<#0x0)      }
0xc0ba00c4  {   e35f0376        R3=and(R3,#0xff)    
0xc0ba00c8      05c5223a        R5=memub(R2+R5<<#0x0)       }
0xc0ba00cc  {   254706ef        R5+=add(R6,R7)  
0xc0ba00d0      03c3223a        R3=memub(R2+R3<<#0x0)       }
0xc0ba00d4  {   e55f0576        R5=and(R5,#0xff)    
0xc0ba00d8      03c463f1        R3=xor(R3,R4)       }
0xc0ba00dc  {   05c5223a        R5=memub(R2+R5<<#0x0)       }
0xc0ba00e0  {   05c5223a        R5=memub(R2+R5<<#0x0)       }
0xc0ba00e4  {   034563f1        R3=xor(R3,R5)   
0xc0ba00e8      5ec2a848        memb(gp+#0x105e)=R3.new     }   < R3.new totally makes sense
```

As you can see, the result is much better now. It's a PoC, so there are some many bugs/errors for sure in my disassembler, 
but for the relevant part of the algorithm it turned out to work just fine, which is what I actually needed. Feel free 
to send some pull requests to my github if you find some bugs or if you need to add features like an emulator :) 

You can grab the latest version of my disassembler over [here](https://github.com/bkerler/qc_modem_tools/blob/master/hexagon_disasm.py).

### Understanding the modem algorithm code flow

Following the code flow in the openlock_cmd function @0xC0B12CC0, we see that if no value is given,  it will first send 
a 8 byte challenge as a response. However if a value is given, an algorithm is being used to determine if the generated 
code corresponds to the value given in the at command.

So having a closer look, a spot catches our eye (the functions weren't named this way as the binary
has no symbols due to being stripped):

```
LOAD:C0B12D58                 4c210020       r1 = add (sp, #8) ; r0 = memw (r2 + #0) }
LOAD:C0B12D5C                 1000402a     { p0 = cmp.eq (r0, #0) ; if (p0.new) jump:nt loc_C0B12DB0
LOAD:C0B12D60                 0c224b8e       immext (#0xC222E380)
LOAD:C0B12D64                 7c84c102       r3:2 = combine (#8, ##aOmarDidThisA71) } @ "OMAR DID THIS...A710"
LOAD:C0B12D68                 78004204     { r4 = #0x10
LOAD:C0B12D6C                 2c202c01       r0 = add (sp, #8) ; r1 = add (sp, #0) }
LOAD:C0B12D70                 5a11e94e     { call secret_algorithm } @ r0 = challenge, r1=buffer, r2=key, r3=bufferlen, r4=keylen
LOAD:C0B12D74                 5b924246     { call compare_challenge
LOAD:C0B12D78                 70724001       r1 = r18
LOAD:C0B12D7C                 28822c00       r2 = #8 ; r0 = add (sp, #0) }
```

We see that at offset @0xC0B12D70 a function (named here secret_algorithm) is being called with a weird string 
"OMAR DID THIS...A710" that has a length of 0x10, and the function has 8 bytes as an input length, which is also 
the corresponding output length.

Having a closer look at the secret_algorithm function, there is a function @0xC0BA0020 (named here SierraInit) 
which takes the weird string (in fact a key) and generates a byte array key table (256 bytes) based on the 
given key bytes (here our weird string).

Returning to our secret_algorithm function at @0xC0BA0024, the key table is being used to generate a new 
table based on the challenge bytes (loop is being run for each challenge byte), which is then being used to 
calculate the right response (also 8 bytes).

```
LOAD:C0BA000C
LOAD:C0BA000C secret_algorithm:                       @ CODE XREF: atcmd_OPENMEP+B0↑p
LOAD:C0BA000C                                         @ secret_algorithm_with_nvitem+84↑p ...
LOAD:C0BA000C                 5b976a1c     { call stack_setup
LOAD:C0BA0010                 a09dc002       allocframe (#0x10) }
LOAD:C0BA0014                 f5004110     { r17:16 = combine (r0, r1) @ r17=challenge, r16=challengelen
LOAD:C0BA0018                 70624000       r0 = r2
LOAD:C0BA001C                 303a3741       r18 = r3 ; r1 = and (r4, #0xFF) }
LOAD:C0BA0020                 5a00c13c     { call SierraInit } @ r0=key, r1=keylen (generates key table)
LOAD:C0BA0024                 1000406c     { p0 = cmp.eq (r0, #0) ; if (p0.new) jump:nt loc_C0BA00FC
LOAD:C0BA0028                 7800c002       r2 = #0 }
LOAD:C0BA002C                 100a4064     { p0 = cmp.eq (r18, #0) ; if (p0.new) jump:nt loc_C0BA00F4
LOAD:C0BA0030                 0c4a525c       immext (#0xC4A49700)
LOAD:C0BA0034                 788be602       r2 = ##result_buffer }
LOAD:C0BA0038                 6012c008     { loop0 (loc_C0BA003C, r18) } @ run loop for r18=r3= 8 times
LOAD:C0BA003C
LOAD:C0BA003C loc_C0BA003C:                           @ DATA XREF: secret_algorithm+2C↑r
LOAD:C0BA003C                 49284c03     { r3 = memub (gp + #0x1060) @ read keytbl[2]
LOAD:C0BA0040                 9b31c024       r4 = memub (r17 ++ #1) } @ pointer to challenge bytes, being increased each loop iteration
LOAD:C0BA0044                 b0034025     { r5 = add (r3, #1)
LOAD:C0BA0048                 48a8c260       memb (gp + #0x1060) = r6.new } @ set keytbl[2], should be r5.new
LOAD:C0BA004C                 76055fe5     { r5 = and (r5, #0xFF)
LOAD:C0BA0050                 49284c26       r6 = memub (gp + #0x1061) @ read keytbl[3]
LOAD:C0BA0054                 3a22c303       r3 = memub (r2 + r3 << #0) }
LOAD:C0BA0058                 f3064303     { r3 = add (r6, r3)
LOAD:C0BA005C                 f3024507       r7 = add (r2, r5)
LOAD:C0BA0060                 48a8c461       memb (gp + #0x1061) = r4.new } @ set keytbl[3], has to be r3.new instead
LOAD:C0BA0064                 76035fe3     { r3 = and (r3, #0xFF)
LOAD:C0BA0068                 49284be0       r0 = memub (gp + #0x105F) @ read keytbl[1]
LOAD:C0BA006C                 4928cbce       r14 = memub (gp + #0x105E) } @ read keytbl[0]
LOAD:C0BA0070                 f302400c     { r12 = add (r2, r0)
LOAD:C0BA0074                 f302430d       r13 = add (r2, r3)
LOAD:C0BA0078                 3a224008       r8 = memub (r2 + r0 << #0)
LOAD:C0BA007C                 3a22c309       r9 = memub (r2 + r3 << #0) }
LOAD:C0BA0080                 f3024e1c     { r28 = add (r2, r14)
LOAD:C0BA0084                 49284c4f       r15 = memub (gp + #0x1062) @ read keytbl[4]
LOAD:C0BA0088                 a10cc900       memb (r12 + #0) = r9 }
LOAD:C0BA008C                 3a224e12     { r18 = memub (r2 + r14 << #0)
LOAD:C0BA0090                 a1adc200       memb (r13 + #0) = r18.new }
LOAD:C0BA0094                 3a224505     { r5 = memub (r2 + r5 << #0)
LOAD:C0BA0098                 a1bcc200       memb (r28 + #0) = r6.new } @ yeah, we know this should be r5.new
LOAD:C0BA009C                 a107c800     { memb (r7 + #0) = r8 }
LOAD:C0BA00A0                 3a22c801     { r1 = memub (r2 + r8 << #0) }
LOAD:C0BA00A4                 f30f4105     { r5 = add (r15, r1)
LOAD:C0BA00A8                 48a8c262       memb (gp + #0x1062) = r6.new } @ set keytbl[4], yes should be r5.new
LOAD:C0BA00AC                 76055fe5     { r5 = and (r5, #0xFF)
LOAD:C0BA00B0                 3a224303       r3 = memub (r2 + r3 << #0)
LOAD:C0BA00B4                 4808c45f       memb (gp + #0x105F) = r4 } @ set keytbl[1], set challenge byte
LOAD:C0BA00B8                 f3034803     { r3 = add (r3, r8)
LOAD:C0BA00BC                 3a224006       r6 = memub (r2 + r0 << #0)
LOAD:C0BA00C0                 3a22ce07       r7 = memub (r2 + r14 << #0) }
LOAD:C0BA00C4                 76035fe3     { r3 = and (r3, #0xFF)
LOAD:C0BA00C8                 3a22c505       r5 = memub (r2 + r5 << #0) }
LOAD:C0BA00CC                 ef064725     { r5 += add (r6, r7)
LOAD:C0BA00D0                 3a22c303       r3 = memub (r2 + r3 << #0) }
LOAD:C0BA00D4                 76055fe5     { r5 = and (r5, #0xFF)
LOAD:C0BA00D8                 f163c403       r3 = xor (r3, r4) } @ xor challenge byte
LOAD:C0BA00DC                 3a22c505     { r5 = memub (r2 + r5 << #0) }
LOAD:C0BA00E0                 3a22c505     { r5 = memub (r2 + r5 << #0) }
LOAD:C0BA00E4                 f1634503     { r3 = xor (r3, r5)
LOAD:C0BA00E8                 48a8c25e       memb (gp + #0x105E) = r4.new } @ set keytbl[0], is r3.new not r4.new
LOAD:C0BA00EC                 7f008000     { nop
LOAD:C0BA00F0                 ab10c308       memb (r16 ++ #1) = r3 }:endloop0
LOAD:C0BA00F4
LOAD:C0BA00F4 loc_C0BA00F4:                           @ CODE XREF: secret_algorithm+20↑j
LOAD:C0BA00F4                 5a00c12c     { call stack_verify }
LOAD:C0BA00F8                 7800c022     { r2 = #1 }
LOAD:C0BA00FC
LOAD:C0BA00FC loc_C0BA00FC:                           @ CODE XREF: secret_algorithm+18↑j
LOAD:C0BA00FC                 0ff45ed4     { immext (#0xFF47B500)
LOAD:C0BA0100                 1702c000       r0 = r2 ; jump stack_dealloc }
LOAD:C0BA0100 @ End of function secret_algorithm
```

As you can see, I used the original IDA Pro 7.4 GSMK plugin output and commented it based on my disassembler. I hope you can now see that having a look
at the status of current hexagon disassemblers, it's not really trivial to emulate or reconstruct code in order to do any exploitation or reverse engineering. 

## Conclusion and Outlook
In the part 2, we had a closer look at issues that come with disassemblers and learned a bit about how to reverse qualcomm hexagon QDSP v6
binaries. We successfully were able to recover the algorithm, which you can make usage of over [here](https://github.com/bkerler/SierraWirelessGen).

In the upcoming Part 3 we will have a closer look at the Netgear MR1100 devices for decrypting
the firmware in order to recover the algorithm key. 

Stay tuned !








