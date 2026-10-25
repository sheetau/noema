"""Render reproducible vector/raster specimens of the opt-in circle script."""
from dataclasses import asdict
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from scripts.circle_alphabet import *

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/alphabet-circle-v1'
SAMPLE='examples/v014/circle-alphabet-samples.noema'
JP='C:/Windows/Fonts/YuGothM.ttc'
LATIN='C:/Windows/Fonts/segoeui.ttf'
INK='#172127';MUTED='#607078';ACCENT='#496f7c';PAPER='#ffffff'
SS=2

class Sheet:
    def __init__(self,width,height):
        self.width,self.height=width,height
        self.image=Image.new('RGB',(width*SS,height*SS),PAPER)
        self.draw=ImageDraw.Draw(self.image)
    def text(self,xy,text,size=22,fill=INK,jp=True):
        self.draw.text(tuple(round(x*SS) for x in xy),text,font=ImageFont.truetype(JP if jp else LATIN,size*SS),fill=fill)
    def rule(self,xy,fill='#e0e7e8',width=1):
        self.draw.line(tuple(round(x*SS) for x in xy),fill=fill,width=max(1,round(width*SS)))
    def geometry(self,shapes,x,y,scale=1,fill=INK):
        for s in shapes:
            if s['kind'] in ('circle','dot'):
                cx=(x+s['x']*scale)*SS;cy=(y+s['y']*scale)*SS;r=s['r']*scale*SS
                self.draw.ellipse((round(cx-r),round(cy-r),round(cx+r),round(cy+r)),outline=fill,
                                  fill=fill if s['kind']=='dot' else None,width=max(1,round(STROKE*scale*SS)))
            else:self.rule((x+s['x1']*scale,y+s['y1']*scale,x+s['x2']*scale,y+s['y2']*scale),fill,STROKE*scale)
    def atoms(self,atoms,x,y,width,scale=.76):
        placements,height=layout(atoms,width,scale)
        for a,shapes,dx,dy in placements:self.geometry(shapes,x+dx,y+dy,scale)
        return height
    def save(self,name):
        self.image.resize((self.width,self.height),Image.Resampling.LANCZOS).save(OUT/name)

def specimens(doc):
    sheet=Sheet(1800,1430)
    sheet.text((76,40),'NOEMA  /  CIRCLE SCRIPT  /  01',19,ACCENT,False)
    sheet.text((72,85),'円と線で書く Noema',42)
    sheet.text((76,150),'現行文法から生成する書体試作。本文の基準線は表示しない。',23,MUTED)
    sheet.rule((76,206,1724,206))
    captions=['アキはナオを信頼する。','ナオはアキを信頼していない。','すべての人には、信頼する誰かがいる。']
    y=244
    for i,(node,caption) in enumerate(zip(doc['statements'],captions),1):
        sheet.text((76,y),f'0{i}',20,ACCENT,False)
        sheet.text((130,y-2),caption,26)
        height=sheet.atoms(statement(node),78,y+82,1640,.76)
        y+=82+height+42
        sheet.rule((76,y-20,1724,y-20))
    sheet.text((76,y+4),'読み分ける部品',24)
    labels=[('assert','主張'),('not','否定'),('forall','すべて'),('exists','存在'),('call','定義の適用'),('variable','変項')]
    for i,(role,label) in enumerate(labels):
        x=100+i*267
        sheet.geometry(glyph(Atom('',role))[0],x,y+88,.9)
        sheet.text((x,y+150),label,21,MUTED)
    sheet.text((76,1326),'例文の規約：aa＝人、ab＝信頼する、ac＝アキ、ad＝ナオ。',20,MUTED)
    sheet.text((76,1364),'構文の役割を字形化し、名前は綴りを保持する。宣言を含む原文・SVG・構造付きデータを付属。',19,MUTED)
    assert y+180<1320,('Specimen overflows',y)
    sheet.save('sentences.png')

    sheet=Sheet(1800,1190)
    sheet.text((76,42),'NOEMA  /  COMPONENTS',19,ACCENT,False)
    sheet.text((72,87),'3段・3サイズ・放射方向の接続',38)
    sheet.text((76,148),'円の中心と横線は同じ3本の基準線上へ。線の方向は縦・横・45度のみ。',23,MUTED)
    for y in (230,278,326):sheet.rule((76,y,1100,y),'#efcdd1')
    for x,r,y,label in [(180,6,278,'小円'),(390,14,278,'中円'),(630,22,278,'大円')]:
        sheet.geometry([circle(0,0,r)],x,y,2)
        sheet.text((x-25,352),label,22,MUTED)
    sheet.geometry(shape(22,24,4),850,230,2)
    sheet.text((1190,235),'基準線は設計用',23)
    sheet.text((1190,278),'文中では非表示',21,MUTED)
    sheet.rule((76,410,1724,410))
    sheet.text((76,446),'名前・数値を綴る32種の部品',27)
    sheet.text((76,495),'同じ綴りは同じ形。字形から未知の語義を推測するものではない。',21,MUTED)
    for index,c in enumerate(ALPHABET):
        x=92+(index%8)*210;y=590+(index//8)*135
        sheet.geometry(spelling(c),x,y,1)
        sheet.text((x+28,y+62),c,20,MUTED,False)
    sheet.text((76,1130),'二重円が綴りの開始を示す。構文の主字と綴りの列を組み合わせ、必要な字形だけを生成する。',21,MUTED)
    sheet.save('components.png')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    text=(ROOT/SAMPLE).read_text(encoding='utf-8');doc=parse(text)
    records=[[asdict(a) for a in row] for row in rows(doc)]
    assert recover(records)==doc
    shapes=[]
    for row in rows(doc):
        for a in row:
            g,_=glyph(a);geometry_check(g);shapes.extend(g)
    (OUT/'sample-complete.svg').write_text(svg_document(text,width=1640,scale=.76),encoding='utf-8',newline='\n')
    (OUT/'sample-atoms.json').write_text(json.dumps(dict(version=VERSION,atoms=records),ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    (ROOT/'data/circle-alphabet-prototype-v1.json').write_text(json.dumps(spec(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    specimens(doc)
    result=dict(version=VERSION,source=SAMPLE,statement_count=3,
                geometry_elements=len(shapes),canonical_ast_roundtrip=True,
                geometry_rules_checked=True,human_legibility_validated=False,
                outputs=[p.relative_to(ROOT).as_posix() for p in sorted(OUT.iterdir()) if p.is_file()],
                output_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir()) if p.is_file()},
                source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in [SAMPLE,'scripts/circle_alphabet.py','scripts/proof_circle_alphabet.py','tests/test_circle_alphabet.py','docs/circle-alphabet-prototype-v1.md','data/circle-alphabet-prototype-v1.json','concept/alphabet-concept.md','concept/noema-alphabet-concept.png']})
    (ROOT/'reports/circle-alphabet-prototype-v1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
