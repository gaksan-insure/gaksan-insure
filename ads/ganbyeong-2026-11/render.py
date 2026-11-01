# 간병인보험 세로 숏폼 광고 렌더러 (1080x1920, 30fps)
# 사용: python3 render.py  (img/s1~s8.png, fonts/, logo.png, music.wav 필요)
import subprocess, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
W,H=1080,1920; FPS=30; XF=0.6
os.makedirs('build',exist_ok=True)
F_SUB='fonts/nm800.ttf'; F_REG='fonts/nm700.ttf'; F_SANS='fonts/ns500.ttf'

# (이미지, 길이, [(문구, 시작, 끝)])
SCENES=[
 ('img/s1.png',5.5,[('자식한테\n짐 되기 싫으시지요?',0.6,5.3)]),
 ('img/s2.png',6.5,[('병원비는 보험이 냅니다.',0.5,3.2),('간병비는 자식이 냅니다.',3.4,6.3)]),
 ('img/s3.png',4.0,[('딸은 회사에\n휴가를 냅니다.',0.4,3.9)]),
 ('img/s4.png',4.0,[('아들은 주말마다\n내려옵니다.',0.4,3.9)]),
 ('img/s5.png',6.0,[('며느리는\n말을 아낍니다.',0.4,3.0),('그리고 다들\n괜찮다고 합니다.',3.2,5.9)]),
 ('img/s6.png',4.5,[('그런데 정작,\n괜찮지 않으실 겁니다.',0.5,4.4)]),
 ('img/s7.png',8.0,[('간병인 보험은\n그 미안함을 대신\n내주는 보험입니다.',0.5,4.2),('간병인을 쓴 날만큼\n보험에서 나옵니다.',4.4,7.9)]),
 ('img/s8.png',6.0,[('다만 한 살 늘 때마다',0.4,2.6),('보험료는 오르고,\n들어갈 문은 좁아집니다.',2.8,5.9)]),
]
END_DUR=8.5

def text_png(path,text,size=64,fill=(255,255,255),font=F_SUB,spacing=26):
    img=Image.new('RGBA',(W,H),(0,0,0,0))
    f=ImageFont.truetype(font,size); d=ImageDraw.Draw(img)
    bb=d.multiline_textbbox((0,0),text,font=f,spacing=spacing,align='center')
    tw,th=bb[2]-bb[0],bb[3]-bb[1]
    x=(W-tw)//2; y=int(H*0.80)-th//2
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); sd=ImageDraw.Draw(sh)
    sd.multiline_text((x,y+3),text,font=f,fill=(0,0,0,200),spacing=spacing,align='center')
    sh=sh.filter(ImageFilter.GaussianBlur(7))
    img=Image.alpha_composite(img,sh); d=ImageDraw.Draw(img)
    d.multiline_text((x,y),text,font=f,fill=fill+(255,),spacing=spacing,align='center')
    img.save(path)

def grad_png(path):
    img=Image.new('RGBA',(W,H),(0,0,0,0)); px=img.load()
    for yy in range(H):
        a=0
        if yy>H*0.55: a=int(190*((yy-H*0.55)/(H*0.45))**1.3)
        if yy<H*0.12: a=max(a,int(90*(1-yy/(H*0.12))))
        for xx in range(0,W): px[xx,yy]=(12,8,4,a)
    img.save(path)

def tag_png(path):
    img=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(img)
    d.text((54,70),'(광고)',font=ImageFont.truetype(F_SANS,30),fill=(255,255,255,170))
    img.save(path)

grad_png('build/grad.png'); tag_png('build/tag.png')

def run(cmd): subprocess.run(cmd,check=True)

clips=[]
for i,(src,dur,subs) in enumerate(SCENES,1):
    inputs=['-loop','1','-t',str(dur),'-i',src,'-loop','1','-t',str(dur),'-i','build/grad.png','-loop','1','-t',str(dur),'-i','build/tag.png']
    zin= i%2==1
    z=f"(1+0.07*t/{dur})" if zin else f"(1.07-0.07*t/{dur})"
    fc=(f"[0:v]scale=1200:2144,setsar=1,format=yuv420p,"
        f"scale=w='trunc(1200*{z}/2)*2':h='trunc(2144*{z}/2)*2':eval=frame,"
        f"crop={W}:{H},"
        "eq=saturation=0.88:contrast=1.04:gamma=0.98,"
        "colorbalance=rs=0.04:gs=0.01:bs=-0.04:rh=0.03:bh=-0.03,"
        "noise=alls=7:allf=t,vignette=PI/5,format=rgba[b];"
        "[b][1:v]overlay[b0];[b0][2:v]overlay[v0]")
    last='v0'
    for j,(txt,s,e) in enumerate(subs):
        p=f'build/sub{i}_{j}.png'; text_png(p,txt)
        inputs+=['-loop','1','-t',str(dur),'-i',p]
        k=3+j
        fc+=(f";[{k}:v]format=rgba,fade=t=in:st={s}:d=0.5:alpha=1,fade=t=out:st={e-0.5}:d=0.5:alpha=1[t{j}];"
             f"[{last}][t{j}]overlay[v{j+1}]")
        last=f'v{j+1}'
    out=f'build/c{i}.mp4'
    run(['ffmpeg','-y','-loglevel','error',*inputs,'-filter_complex',fc,'-map',f'[{last}]','-r',str(FPS),'-t',str(dur),
         '-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',out])
    clips.append((out,dur)); print('scene',i,'ok',flush=True)

# 엔드카드: 크림 배경 + 로고 + 문구
def endcard():
    bg=(243,237,228); ink=(58,44,34)
    base=Image.new('RGBA',(W,H),bg+(255,))
    logo=Image.open('logo.png').convert('RGBA').resize((300,300),Image.LANCZOS)
    flat=Image.new('RGB',logo.size,(255,255,255)); flat.paste(logo,mask=logo.split()[3])
    region=base.crop(((W-300)//2,250,(W-300)//2+300,550)).convert('RGB')
    base.paste(ImageChops.multiply(region,flat),((W-300)//2,250)); base.save('build/end_bg.png')
    def layer(path,text,y,size,font,fill=ink,spacing=24):
        im=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(im); f=ImageFont.truetype(font,size)
        bb=d.multiline_textbbox((0,0),text,font=f,spacing=spacing,align='center')
        d.multiline_text(((W-(bb[2]-bb[0]))//2,y),text,font=f,fill=fill+(255,),spacing=spacing,align='center'); im.save(path)
    layer('build/e1.png','지금 가진 보험부터\n같이 보겠습니다.',700,66,F_SUB)
    layer('build/e2.png',"'간병' 두 글자만\n답장 주세요.",960,66,F_SUB,fill=(150,72,40))
    layer('build/e3.png','각산보험대리점 대표 김대인',1300,44,F_REG)
    layer('build/e4.png','☎ 010-8362-5177',1380,58,F_SANS)
    layer('build/e5.png','보험계약 체결 전 상품설명서 및 약관을 반드시 읽어보시기 바랍니다.\n가입 조건과 보장 내용은 상품별로 다를 수 있습니다.',1740,24,F_SANS,fill=(120,105,92),spacing=12)
    layer('build/e6.png','(광고)',70,30,F_SANS,fill=(120,105,92))
endcard()
d=END_DUR
ins=['-loop','1','-t',str(d),'-i','build/end_bg.png']
for k in range(1,7): ins+=['-loop','1','-t',str(d),'-i',f'build/e{k}.png']
times=[(1,0.5),(2,2.3),(3,4.2),(4,4.2),(5,4.6),(6,0.0)]
fc='[0:v]format=rgba[b0]'
for n,(k,s) in enumerate(times):
    fc+=f";[{k}:v]format=rgba,fade=t=in:st={s}:d=0.8:alpha=1[l{n}];[b{n}][l{n}]overlay[b{n+1}]"
fc+=f";[b{len(times)}]noise=alls=4:allf=t,format=yuv420p[vout]"
run(['ffmpeg','-y','-loglevel','error',*ins,'-filter_complex',fc,'-map','[vout]','-r',str(FPS),'-t',str(d),
     '-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','build/c9.mp4'])
clips.append(('build/c9.mp4',d)); print('end ok',flush=True)

# xfade 연결 + 음악
ins=[]; 
for p,_ in clips: ins+=['-i',p]
fc=''; prev='0:v'; off=0
for n in range(1,len(clips)):
    off+=clips[n-1][1]-XF
    fc+=f"[{prev}][{n}:v]xfade=transition=fade:duration={XF}:offset={off:.3f}[x{n}];"
    prev=f'x{n}'
total=sum(c[1] for c in clips)-XF*(len(clips)-1)
fc+=f"[{prev}]fade=t=in:st=0:d=0.8,fade=t=out:st={total-1.0:.2f}:d=1.0[vout];"
fc+=f"[{len(clips)}:a]atrim=0:{total:.2f},afade=t=out:st={total-2.5:.2f}:d=2.5,volume=0.9[aout]"
run(['ffmpeg','-y','-loglevel','error',*ins,'-i','music.wav','-filter_complex',fc,'-map','[vout]','-map','[aout]',
     '-c:v','libx264','-preset','medium','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart','final.mp4'])
print('TOTAL',total)
