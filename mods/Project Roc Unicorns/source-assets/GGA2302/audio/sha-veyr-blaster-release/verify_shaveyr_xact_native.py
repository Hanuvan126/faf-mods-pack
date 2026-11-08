import ctypes as C,uuid
from pathlib import Path
V=C.c_void_p;U=C.c_uint32;H=C.c_uint16;HRESULT=C.c_int32
class GUID(C.Structure):_fields_=[('raw',C.c_ubyte*16)]
def guid(s):return GUID.from_buffer_copy(uuid.UUID(s).bytes_le)
def call(obj,index,ret,args,*values):
 table=C.cast(obj,C.POINTER(C.POINTER(V))).contents
 return C.WINFUNCTYPE(ret,V,*args)(table[index])(obj,*values)
def check(label,hr):
 print(label,hex(hr&0xffffffff),flush=True)
 assert hr>=0,label
class Params(C.Structure):
 _fields_=[('lookAheadTime',U),('settings',V),('size',U),('flags',U),('alloc',U),('read',V),('result',V),('notify',V),('renderer',V),('xaudio',V),('master',V)]
ole=C.OleDLL('ole32');ole.CoInitialize(None)
cls=guid('3b80ee2a-b0f5-4780-9e30-90cb39685b03');iid=guid('9e33f661-2d07-43ec-9704-bbcb71a54972')
engine=V();check('CoCreate XACT3.0',ole.CoCreateInstance(C.byref(cls),None,1,C.byref(iid),C.byref(engine)))
globaldata=C.create_string_buffer(Path('D:/SteamLibrary/steamapps/common/Supreme Commander Forged Alliance/sounds/SupCom.xgs').read_bytes())
params=Params();params.lookAheadTime=250;params.settings=C.cast(globaldata,V);params.size=len(globaldata)-1
check('Initialize with FA globals',call(engine,6,HRESULT,[C.POINTER(Params)],C.byref(params)))
folder=Path('audio_tools/sha_veyr_release')
wb=C.create_string_buffer((folder/'PRU_ShaVeyr.xwb').read_bytes());sb=C.create_string_buffer((folder/'PRU_ShaVeyr.xsb').read_bytes())
wavebank=V();soundbank=V()
check('Create wave bank',call(engine,10,HRESULT,[V,U,U,U,C.POINTER(V)],wb,len(wb)-1,0,0,C.byref(wavebank)))
check('Create sound bank',call(engine,9,HRESULT,[V,U,U,U,C.POINTER(V)],sb,len(sb)-1,0,0,C.byref(soundbank)))
index=call(soundbank,0,H,[C.c_char_p],b'ShaVeyr_Blaster');print('Cue index',index,flush=True);assert index==0
cue=V();check('Prepare cue',call(soundbank,3,HRESULT,[H,U,U,C.POINTER(V)],index,0,0,C.byref(cue)))
# Test five simultaneous/overlapping native voices with output muted.
import time
matrix=(C.c_float*2)(0,0)
check('Mute test cue',call(cue,4,HRESULT,[U,U,C.POINTER(C.c_float)],1,2,matrix))
check('Play test cue',call(cue,0,HRESULT,[]))
voices=[cue]
for i in range(4):
 time.sleep(.1)
 check('DoWork',call(engine,8,HRESULT,[]))
 v=V();check('Prepare next shot',call(soundbank,3,HRESULT,[H,U,U,C.POINTER(V)],index,0,0,C.byref(v)))
 check('Mute next shot',call(v,4,HRESULT,[U,U,C.POINTER(C.c_float)],1,2,matrix))
 check('Play next shot',call(v,0,HRESULT,[]));voices.append(v)
for v in voices:
 check('Stop test cue',call(v,1,HRESULT,[U],1))
 check('Destroy test cue',call(v,3,HRESULT,[]))
check('Destroy soundbank',call(soundbank,6,HRESULT,[]))
check('Destroy wavebank',call(wavebank,0,HRESULT,[]))
check('Shutdown',call(engine,7,HRESULT,[]))
call(engine,2,U,[])
print('Native XACT accepts the generated bank and resolves/prepares its cue.')
