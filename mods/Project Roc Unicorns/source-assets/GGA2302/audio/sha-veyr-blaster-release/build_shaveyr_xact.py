from pathlib import Path
import struct,wave,numpy as np,json
P=lambda fmt,*v:struct.pack('<'+fmt,*v)
out=Path('audio_tools/sha_veyr_release');out.mkdir(exist_ok=True)
name='PRU_ShaVeyr';cue='ShaVeyr_Blaster'
p=Path('F:/FAF-Development/work/faf-upload/mods/Project Roc Unicorns/source-assets/GGA2302/audio/sha-veyr-blaster-low-v2/A_blaster_shot_01.wav')
with wave.open(str(p),'rb') as w:
 sr=w.getframerate();x=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)/32768
x*=10**(1/20)
assert np.max(np.abs(x))<.75
pcm=np.round(x*32767).astype('<i2').tobytes()
# Version 43 / header 42 matches the installed FA banks. PCM16 mono, no streaming.
seg0=52;seg1=148;dataoff=172
wbname=name.encode().ljust(64,b'\0')
segments=[(seg0,96),(seg1,24),(dataoff,0),(0,0),(dataoff,len(pcm))]
wb=b'WBND'+P('II',43,42)+b''.join(P('II',*v) for v in segments)
wb+=P('II',0,1)+wbname+P('IIIIQ',24,64,4,0,0)
wb+=P('6I',len(x)<<4,(1<<2)|(sr<<5)|(2<<23)|(1<<31),0,len(pcm),0,0)+pcm
assert len(wb)==dataoff+len(pcm)
(out/(name+'.xwb')).write_bytes(wb)
# A simple one-wave sound with native weapon category and attenuation RPCs.
# Codes refer to FA's global SupCom.xgs; no stock audio is distributed.
soundoff=202
rpc=P('HBIII',15,3,918,1355,1437)
sound=P('BHBhBH',2,6,120,0,0,27)+P('HB',0,0)+rpc
assert len(sound)==27
cueoff=soundoff+len(sound)
cuerecord=P('BII BHHB',5,soundoff,0,32,0,0,0)
hashoff=cueoff+len(cuerecord);indexoff=hashoff+32;namesoff=indexoff+6
# One cue: all hash buckets resolve to the sole entry, terminated at 0xffff.
hashes=P('16H',*([0]*16));index=P('IH',namesoff,65535)
header=b'SDBK'+P('HHHQBHHHHBH HH',43,43,0,0,1,0,1,0,16,1,1,len(cue)+1,0)
assert len(header)==34
header+=P('10i',-1,cueoff,namesoff,-1,-1,-1,138,hashoff,indexoff,soundoff)+wbname
assert len(header)==138
sb=header+wbname+sound+cuerecord+hashes+index+cue.encode()+b'\0'
crc=65535
for byte in sb[18:]:
 crc ^= byte
 for _ in range(8): crc=(crc>>1) ^ (0x8408 if crc&1 else 0)
sb=sb[:8]+P('H',crc^65535)+sb[10:]
(out/(name+'.xsb')).write_bytes(sb)
with wave.open(str(out/'ShaVeyr_Blaster.wav'),'wb') as w:
 w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(pcm)
print('Built',len(sb),'byte XSB,',len(wb),'byte XWB. Peak',20*np.log10(max(abs(x))),'dBFS')
