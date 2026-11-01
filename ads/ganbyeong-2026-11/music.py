import numpy as np, wave
SR=44100; DUR=49.0
N=int(SR*DUR); L=np.zeros(N); R=np.zeros(N)
def mtof(m): return 440*2**((m-69)/12)
rng=np.random.default_rng(7)
def piano(t0,m,vel=0.5,length=4.0,pan=0.0):
    f=mtof(m); n=int(length*SR); t=np.arange(n)/SR
    s=np.zeros(n)
    for k,a in enumerate([1,0.55,0.32,0.18,0.10,0.06,0.03],1):
        fk=f*k*np.sqrt(1+0.0004*k*k)
        dec=np.exp(-t*(0.9+0.55*k)*(f/260)**0.35)
        s+=a*np.sin(2*np.pi*fk*t+rng.random()*6)*dec
    att=np.minimum(1,t/0.004); s*=att
    s+=0.02*rng.standard_normal(n)*np.exp(-t*60)  # hammer
    rel=np.ones(n); rl=int(0.3*SR); rel[-rl:]=np.linspace(1,0,rl); s*=rel
    i=int(t0*SR); e=min(N,i+n); s=s[:e-i]*vel
    L[i:e]+=s*(1-pan)/1.0; R[i:e]+=s*(1+pan)/1.0
def pad(t0,ms,length,vel=0.05):
    n=int(length*SR); t=np.arange(n)/SR; s=np.zeros(n)
    for m in ms:
        for d in (-0.06,0.06):
            f=mtof(m)*2**(d/12)
            for k in range(1,6): s+=np.sin(2*np.pi*f*k*t+rng.random()*6)/k**1.6
    env=np.minimum(1,t/1.5)*np.minimum(1,(length-t)/1.5)
    s*=env*vel/len(ms)
    i=int(t0*SR); e=min(N,i+n); L[i:e]+=s[:e-i]; R[i:e]+=s[:e-i]
# chords (root bass, voicing) in A minor -> warmer turn
beat=60/66
prog=[('Am0',45,[57,60,64]),('Am',45,[57,60,64]),('F',41,[57,60,65]),('C',48,[55,60,64]),('G',43,[55,59,62]),
      ('Am',45,[57,60,64]),('F',41,[57,60,65]),('Dm',38,[57,62,65]),('E',40,[56,59,64]),
      ('F',41,[60,65,69]),('C',48,[60,64,67]),('G',43,[59,62,67]),('Am',45,[60,64,69]),
      ('F',41,[60,65,69]),('G',43,[59,62,67]),('C',36,[60,64,67])]
melody={-1:[None,None,None,None],0:[76,None,74,72],1:[72,None,None,69],2:[67,None,72,None],3:[71,None,None,None],
        4:[76,None,74,72],5:[72,None,74,76],6:[77,None,76,74],7:[71,None,None,None],
        8:[72,74,76,None],9:[79,None,76,None],10:[74,None,76,77],11:[76,None,None,72],
        12:[72,None,74,76],13:[74,None,None,None],14:[72,None,None,None]}
t=0.6; bar=4*beat*0.82
for idx,(name,root,voic) in enumerate(prog):
    last= idx==len(prog)-1
    piano(t,root,0.42,6.0,-0.2)
    for j,m in enumerate(voic):
        piano(t+beat*0.82*(1+j*0.5),m,0.20,4.5,0.1*j)
    for j,m in enumerate(melody[idx-1]):
        if m: piano(t+j*beat*0.82,m,0.30 if idx>=9 else 0.24,5.0 if last else 3.5,0.25)
    if idx>=9: pad(t,[root+12]+voic,bar+1.5,0.06)
    t+=bar if not last else 0
x=np.stack([L,R],1)
# simple reverb: feedback comb taps
out=x.copy()
for d,g in [(0.031,0.35),(0.047,0.3),(0.071,0.25),(0.113,0.22),(0.167,0.18),(0.241,0.14),(0.353,0.1)]:
    k=int(d*SR); out[k:]+=x[:-k]*g
out*= np.minimum(1,np.arange(N)/SR/0.3)[:,None]
fade=np.ones(N); fl=int(3*SR); fade[-fl:]=np.linspace(1,0,fl); out*=fade[:,None]
out/=np.abs(out).max()*1.12
w=wave.open('music.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((out*32767).astype('<i2').tobytes()); w.close()
print('bar sec',bar,'end t',t)
