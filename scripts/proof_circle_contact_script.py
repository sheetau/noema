"""Render and record the revised circle-contact rules, without image generation."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from scripts.circle_contact_script import *

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/alphabet-circle-v3'
SOURCE='examples/v014/circle-contact-samples.noema'
PROFILE='data/connected-circle-reading-v2.json'
SS=3
INK='#182c2e';MUTED='#657c7d';ACCENT='#487c79'
CAPTIONS=['アキはナオを助ける。','アキはナオを信頼する。','アキはナオを信頼し、助ける。',
          'アキがナオを信頼するなら、ナオはアキを助ける。','アキとナオは、互いを信頼する。',
          'アキはナオを信頼していない。','アキはナオを信頼するか、助ける（両方でもよい）。',
          'アキはナオに肯定的な見込みを持つが、選択をナオに依存させない。']


class Sheet:
    def __init__(self,width,height):
        self.width,self.height=width,height
        self.image=Image.new('RGB',(width*SS,height*SS),'#fffffe')
        self.draw=ImageDraw.Draw(self.image)
    def text(self,x,y,text,size=22,color=INK,jp=True):
        path='C:/Windows/Fonts/YuGothM.ttc' if jp else 'C:/Windows/Fonts/segoeui.ttf'
        self.draw.text((round(x*SS),round(y*SS)),text,font=ImageFont.truetype(path,size*SS),fill=color)
    def rule(self,a,b,color='#e3e9e6',width=1):
        self.draw.line([(round(x*SS),round(y*SS)) for x,y in (a,b)],fill=color,width=max(1,round(width*SS)))
    def shape(self,shapes,x,y,scale=1):
        for s in shapes:
            if s['kind']=='circle':
                cx,cy,r=(x+s['x']*scale)*SS,(y+s['y']*scale)*SS,s['r']*scale*SS
                # Pillow outlines are inset; expand so the stroke is centered
                # on the exact circle, as in SVG, including at tangencies.
                r+=STROKE*scale*SS/2
                self.draw.ellipse(tuple(round(v) for v in (cx-r,cy-r,cx+r,cy+r)),outline=INK,width=max(1,round(STROKE*scale*SS)))
            else:
                self.rule((x+s['x1']*scale,y+s['y1']*scale),(x+s['x2']*scale,y+s['y2']*scale),INK,STROKE*scale)
    def save(self,name):
        self.image.resize((self.width,self.height),Image.Resampling.LANCZOS).save(OUT/name)


@lru_cache(maxsize=1)
def result():
    return compile_document((ROOT/SOURCE).read_text(encoding='utf-8'),json.loads((ROOT/PROFILE).read_text(encoding='utf-8')))


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    data=result();sentences=data['sentences']
    sheet=Sheet(1700,1580)
    sheet.text(72,36,'NOEMA  /  CIRCLE CONTACT  /  03',18,ACCENT,False)
    sheet.text(70,83,'円の接触と、円ごとの接続で書く。',36)
    sheet.text(74,142,'更新されたコンセプトに基づく例文。すべて同じ意味規則と配置計算から生成。',21,MUTED)
    sheet.rule((74,190),(1626,190))
    for i in range(5):
        y=224+i*244
        sheet.text(74,y,f'{i+1:02}',18,ACCENT,False)
        sheet.text(125,y-3,CAPTIONS[i],24)
        sheet.shape(sentences[i]['shapes'],70,y+66,1.65)
        sheet.rule((74,y+220),(1626,y+220))
    sheet.text(74,1470,'「信頼」は、肯定的な見込みと、自分の選択を相手に依存させることの連言という局所解釈。',20,MUTED)
    sheet.text(74,1510,'円周で止まる接続・中心から出る接続・接触を使い分ける。点・矢印・線だけの輪は使わない。',20,MUTED)
    sheet.save('sentences.png')

    sheet=Sheet(1700,870)
    for i,y in zip((1,2,3,4),(80,280,480,680)):
        sheet.shape(sentences[i]['shapes'],70,y,1.65)
    sheet.save('writing.png')

    sheet=Sheet(1700,1320)
    sheet.text(72,36,'NOEMA  /  GEOMETRY & GRAMMAR',18,ACCENT,False)
    sheet.text(70,83,'接触条件を、寸法と生成規則にする。',34)
    sheet.text(74,145,'罫線間隔 h＝32。中円 r＝h／√2、小円 r＝h−h／√2、大円 r＝3h／√2−h。',22,MUTED)
    geometry=[circle(48,0,SMALL),circle(48,32,MEDIUM),circle(150,0,MEDIUM),circle(182,32,MEDIUM),
              circle(290,32,LARGE),circle(290+LARGE,32,SMALL)]
    for y in RAILS:sheet.rule((74,230+y*2.1),(850,230+y*2.1),'#ecdadd')
    sheet.shape(geometry,74,230,2.1)
    sheet.text(900,233,'小円＋中円：上下で接する',22)
    sheet.text(900,279,'中円＋中円：45度方向で接する',22)
    sheet.text(900,325,'大円＋小円：円周上に中心',22)
    sheet.text(74,414,'同心円は異なるサイズのみ。大円の中心は必ず中央の罫線上。許可されない重なりは拒否する。',20,MUTED)
    sheet.rule((74,470),(1626,470))
    for n,index in enumerate((5,7,6)):
        y=503+n*238
        sheet.text(74,y,CAPTIONS[index],23)
        sheet.shape(sentences[index]['shapes'],70,y+65,1.5)
    sheet.text(74,1235,'範囲の入口・出口を、円周／中心への接続の組で区別する。接続方法の違いが文法を担う。',20,MUTED)
    sheet.save('geometry-and-scope.png')
    for i in range(len(sentences)):
        (OUT/f'sentence-{i+1:02}.svg').write_text(svg(data,i),encoding='utf-8',newline='\n')
    (OUT/'structure.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    from scripts.proof_circle_contact_papers import prepare as prepare_papers
    prepare_papers()


def build_report():
    data=result()
    files=[SOURCE,PROFILE,'scripts/circle_contact_script.py','scripts/proof_circle_contact_script.py',
           'scripts/connected_circle_script.py','tests/test_circle_contact_script.py','docs/circle-contact-script-v3.md',
           'concept/alphabet-concept.md','concept/noema-alphabet-concept.png',
           'scripts/proof_circle_contact_papers.py',
           'data/einstein-light-roundtrip-definition-source-reading-v1.json',
           'data/einstein-final-transform-source-reading-v1.json','data/public-first-sentence-reading-v1.json',
           'examples/v014/einstein-reviewed-complete-v1.noema','examples/v016/kant-reviewed-complete-v1.noema']
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    outputs=[OUT/name for name in ('sentences.png','writing.png','geometry-and-scope.png','structure.json')]
    outputs += [OUT/f'sentence-{i+1:02}.svg' for i in range(len(data['sentences']))]
    outputs += [OUT/name for name in ('paper-equations.png','paper-quotations.png','paper-specimens.json',
                                     'paper-equation-01.svg','paper-equation-02.svg')]
    return dict(schema='noema-circle-contact-proof-3',renderer=VERSION,
                source_sha256={f:digest(ROOT/f) for f in files},
                output_sha256={f.relative_to(ROOT).as_posix():digest(f) for f in outputs},
                dimensions=dict(pitch=PITCH,small=SMALL,medium=MEDIUM,large=LARGE),
                sentences=[dict(width=s['width'],circles=sum(p['kind']=='circle' for p in s['shapes']),
                                line_topology=line_topology([p for p in s['shapes'] if p['kind']=='line'])) for s in data['sentences']],
                limits=['Same supported semantic fragment as draft 02; no new manuscript coverage',
                        'Geometric checks do not establish unique optical decoding or aesthetic acceptance'])


if __name__=='__main__':
    prepare()
    print(json.dumps(build_report(),ensure_ascii=False,indent=2))
