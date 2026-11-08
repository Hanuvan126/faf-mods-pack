from pathlib import Path
import numpy as np,wave,json
SR=48000
out=Path('F:/FAF-Development/work/faf-upload/mods/Project Roc Unicorns/source-assets/GGA2302/audio/sha-veyr-blaster-low-v2')
out.mkdir(parents=True,exist_ok=True)
def noise(rng,n,lo,hi):
 f=np.fft.rfftfreq(n,1/SR);h=(1-np.exp(-(f/lo)**4))*np.exp(-(f/hi)**6)
 y=np.fft.irfft(np.fft.rfft(rng.normal(size=n))*h,n)
 return y/(np.std(y)+1e-9)
def ph(f):return 2*np.pi*np.cumsum(f)/SR
def make(kind,seed):
 rng=np.random.default_rng(seed);t=np.arange(int(.45*SR))/SR;n=len(t)
 if kind=='A_blaster':
  # Single clean sliding laser voice: fast pitch movement, no metallic overtones.
  p=ph((280+2500*np.exp(-t/.021))*2**(-10/12))
  gate=(1-np.exp(-t/.0018))*np.exp(-(t/.068)**1.6)
  x=np.tanh(1.8*np.sin(p))*gate*.48
  x+=.08*noise(rng,n,1800,6000)*np.exp(-t/.014)
 elif kind=='B_rail':
  # Broadband railgun crack with a dense air displacement, no pitched drum body.
  x=.65*noise(rng,n,220,3300)*(1-np.exp(-t/.0008))*np.exp(-(t/.022)**1.3)
  x+=.12*noise(rng,n,1500,6500)*(1-np.exp(-t/.006))*np.exp(-t/.060)
 elif kind=='C_liquid':
  # Elastic liquid/plasma flick, two opposed pitch curves give a rounded 'vwip'.
  p=ph(420+1850*np.exp(-((t-.018)/.013)**2))
  q=ph(560+1100*np.exp(-t/.018))
  env=(1-np.exp(-t/.003))*np.exp(-(t/.060)**2)
  x=(.42*np.sin(p)+.18*np.sin(q))*env
  x+=.08*noise(rng,n,500,2500)*env
 elif kind=='D_overdrive':
  # Ragged low-mid energy burst, deliberately neither a bell nor a bass kick.
  f=240+330*np.minimum(t/.045,1)
  p=ph(f);raw=np.sin(p)+.45*np.sin(2*p)+.22*np.sin(3*p)
  knots=np.arange(0,.5,.0035)
  texture=np.interp(t,knots,rng.uniform(.15,1,len(knots)))
  env=(1-np.exp(-t/.004))*np.exp(-(t/.080)**3)
  x=.40*np.tanh(4*raw)*texture*env
  x+=.12*noise(rng,n,700,4300)*env
 f=np.fft.rfftfreq(n,1/SR)
 x=np.fft.irfft(np.fft.rfft(x)*(1-np.exp(-(f/90)**4))*np.exp(-(f/8000)**6),n)
 x[:48]*=np.linspace(0,1,48);x[-1200:]*=np.linspace(1,0,1200)
 return x
report=[]
def write(name,x):
 assert np.isfinite(x).all() and max(abs(x))<1
 with wave.open(str(out/name),'wb') as w:
  w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes(np.round(x*32767).astype('<i2').tobytes())
 with wave.open(str(out/name),'rb') as w:assert w.getnframes()==len(x)
for kind in ['A_blaster']:
 shots=[make(kind,1080+i) for i in range(5)]
 gain=min(.19/np.sqrt(np.mean(shots[0][:4800]**2)),.78/max(np.max(np.abs(s)) for s in shots))
 shots=[s*gain for s in shots];demo=np.zeros(int(5*SR));times=[]
 for start in [.2,3.7]:
  for i,s in enumerate(shots):
   time=start+i*.1;pos=round(time*SR);demo[pos:pos+len(s)]+=s;times.append(round(time,2))
 peak=max(abs(demo))
 if peak>.9:
  g=.9/peak;demo*=g;shots=[s*g for s in shots]
 for i,s in enumerate(shots):write(f'{kind}_shot_{i+1:02}.wav',s)
 write(f'{kind}_fast_preview.wav',demo)
 report.append({'variant':kind,'onsets':times,'peak':float(max(abs(demo))),'sample_rate':SR})
(out/'validation.json').write_text(json.dumps(report,indent=2))
(out/'README.txt').write_text('Blaster variant A, oscillator frequencies lowered by ten semitones. Original durations and shot timing preserved. Two five-shot bursts each preview; 0.1 s spacing; burst starts 3.5 s apart. 48kHz PCM16 mono. Not integrated into game.\n')
(out/'synth_shaveyr_blaster_lower.py').write_text(Path(__file__).read_text(encoding='utf-8-sig'))
print(json.dumps(report,indent=2))
