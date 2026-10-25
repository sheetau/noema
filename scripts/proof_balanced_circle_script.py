"""One compact, ruled specimen sheet: ordinary language, Kant and Einstein."""
from copy import deepcopy
from collections import Counter
from functools import lru_cache
import hashlib
from html import escape
import json
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont
from noema.constructed import parse
from scripts.balanced_circle_script import VERSION, compile_expression, pack_lines, PITCH, STROKE, MIN_RUN, MIN_GAP, SMALL, LARGE, nucleus, geometry_check
from scripts.proof_circle_contact_papers import paper_data

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/alphabet-circle-v9'
SOURCE='examples/v016/branch-circle-samples.noema'
KANT='examples/v016/kant-reviewed-complete-v1.noema'
SCALE=.48
SS=3
INK='#203438';MUTED='#65767a';ACCENT='#477d78';GUIDE='#eee5e5'
CAPTIONS=['町に雨が降っている。','一羽の鳥が木の上にいる。','アキが本をナオに渡す。',
          '赤くて丸い果実がある。','すべての鳥が飛ぶわけではない。','町に雨が降れば、アキは家にいる。']
READING={
    'rain':'指定した場所で雨が降っている','above':'第一項が第二項の上方に位置する',
    'give':'第一項が第二項を第三項へ渡す','fruit':'果実である','red':'赤い','round':'丸い',
    'bird':'鳥である','fly':'飛んでいる','inside':'第一項が第二項の内部にいる',
    'town':'例文の町','birdone':'例文で指定された一羽の鳥','treeone':'例文の木',
    'aki':'アキ','book':'例文の本','nao':'ナオ','home':'例文の家',
}
STYLES={'rain':'event','above':'vertical','give':'transfer','inside':'containment'}


@lru_cache(maxsize=1)
def specimens():
    normal=parse((ROOT/SOURCE).read_text(encoding='utf-8'))
    data=paper_data()
    kant=parse((ROOT/KANT).read_text(encoding='utf-8'))
    declarations={d['name']:d for d in kant['declarations']}
    normal_registry={d['name']:i for i,d in enumerate(normal['declarations'])}
    kant_registry={d['name']:i for i,d in enumerate(kant['declarations'])}
    math_registry={name:i for i,name in enumerate(data['quantities'])}
    entries=[]
    for i,statement in enumerate(normal['statements']):
        entries.append(dict(section='normal',label=CAPTIONS[i],compiled=compile_expression(statement,STYLES,normal_registry),
                            source=SOURCE,statement=i))
    for name,label in [('r2lg','① 主張内容の提示（定義参照を含む）'),('r2lo','② 対比・強調・条件・発話の関係')]:
        original=dict(kind='assert',body=dict(kind='call',symbol=name,arguments=[]))
        assert original in kant['statements']
        declaration=declarations[name]
        assert declaration['kind']=='definition' and not declaration['parameters']
        # Expand just the asserted zero-argument definition. Quoted syntax and
        # its definition references remain EXACTLY as registered.
        body=dict(kind='assert',body=deepcopy(declaration['body']))
        entries.append(dict(section='kant',label=label,compiled=compile_expression(body,reference_order=kant_registry),
                            source=KANT,original_assertion=original,expanded_definition=name,display_role='main-assertion'))
    entries.append(dict(section='kant',label='③ 補助：②が参照する後半の定義を展開（再掲）',
                        compiled=compile_expression(declarations['r2ll']['body'],reference_order=kant_registry),
                        source=KANT,definition='r2ll',display_role='expanded-reference',referenced_by='r2lo'))
    for equation in data['equations']:
        entries.append(dict(section='einstein',label=equation['printed'],
                            compiled=compile_expression(equation['expression'],reference_order=math_registry),
                            source=equation['source'],unit=equation['unit'],page=equation['page']))
    return dict(version=VERSION,entries=entries,ordinary_source=normal,ordinary_reading=READING,
                kant_quote=data['kant']['text'],math_quantities=data['quantities'],ordinary_styles=STYLES)


@lru_cache(maxsize=1)
def layout_comparison():
    rows=[]
    for entry in specimens()['entries']:
        c=entry['compiled']
        ordinary=compile_expression(c['source'],reference_order=c['reference_order'],compact_columns=False)
        rows.append(dict(section=entry['section'],columns=c['columns'],width=c['width'],
                         without_columns=ordinary['width'],saved=ordinary['width']-c['width']))
    return rows


class Sheet:
    def __init__(self,width,height):
        self.width,self.height=width,height
        self.image=Image.new('RGB',(width*SS,height*SS),'#fffffe')
        self.draw=ImageDraw.Draw(self.image)
        self.elements=[]
    def text(self,x,y,text,size=20,color=INK,jp=True):
        font=ImageFont.truetype('C:/Windows/Fonts/YuGothM.ttc' if jp else 'C:/Windows/Fonts/segoeui.ttf',size*SS)
        self.draw.text((round(x*SS),round(y*SS)),text,font=font,fill=color)
        self.elements.append(f'<text x="{x}" y="{y+size}" font-size="{size}" fill="{color}">{escape(text)}</text>')
    def rule(self,a,b,color=GUIDE,width=.7):
        self.draw.line([(round(x*SS),round(y*SS)) for x,y in (a,b)],fill=color,width=max(1,round(width*SS)))
        self.elements.append(f'<path d="M {a[0]} {a[1]} L {b[0]} {b[1]}" stroke="{color}" stroke-width="{width}" fill="none"/>')
    def shape(self,shapes,x,y):
        for s in shapes:
            if s['kind']=='line':
                self.rule((x+s['x1']*SCALE,y+s['y1']*SCALE),(x+s['x2']*SCALE,y+s['y2']*SCALE),INK,STROKE*SCALE)
            else:
                cx,cy,r=x+s['x']*SCALE,y+s['y']*SCALE,s['r']*SCALE
                bound=r+STROKE*SCALE/2
                self.draw.ellipse(tuple(round(v*SS) for v in (cx-bound,cy-bound,cx+bound,cy+bound)),outline=INK,width=max(1,round(STROKE*SCALE*SS)))
                self.elements.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{INK}" stroke-width="{STROKE*SCALE}" fill="none"/>')
    def formula(self,x,y,index):
        italic=ImageFont.truetype('C:/Windows/Fonts/timesi.ttf',28*SS)
        roman=ImageFont.truetype('C:/Windows/Fonts/times.ttf',28*SS)
        small=ImageFont.truetype('C:/Windows/Fonts/times.ttf',17*SS)
        cursor=x*SS;baseline=(y+28)*SS
        def put(text,px,py,font,size,italic_style=False):
            self.draw.text((round(px),round(py)),text,font=font,fill=INK,anchor='ls')
            self.elements.append(f'<text x="{px/SS}" y="{py/SS}" font-family="Times New Roman,serif" font-style="{"italic" if italic_style else "normal"}" font-size="{size}" fill="{INK}">{escape(text)}</text>')
        if index:
            put('ξ = β(x − vt)',cursor,baseline,italic,28,True);return
        for token in [('B',False),' − ',('A',False),' = ',('A',True),' − ',('B',False)]:
            if isinstance(token,str):
                put(token,cursor,baseline,roman,28);cursor+=self.draw.textlength(token,font=roman)
            else:
                subscript,prime=token
                put('t',cursor,baseline,italic,28,True);cursor+=self.draw.textlength('t',font=italic)+SS
                put(subscript,cursor,baseline+7*SS,small,17)
                if prime:put('′',cursor,baseline-4*SS,roman,28)
                cursor+=max(self.draw.textlength(subscript,font=small),self.draw.textlength('′',font=roman) if prime else 0)+2*SS
    def writing(self,entry,x,y,width):
        compiled=entry['compiled']
        rows=pack_lines(compiled,width,SCALE)
        for row_index,row in enumerate(rows):
            baseline=y+row_index*66
            for rail in (0,PITCH,2*PITCH):self.rule((x,baseline+rail*SCALE),(x+width,baseline+rail*SCALE))
            self.shape(row['shapes'],x,baseline)
        entry['display']=dict(x=x,y=y,width=width,rows=len(rows),height=len(rows)*66)
        return len(rows)*66
    def save(self,data):
        self.image.resize((self.width,self.height),Image.Resampling.LANCZOS).save(OUT/'overview.png')
        metadata=escape(json.dumps(data,ensure_ascii=False,separators=(',',':')))
        svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}">'
             f'<metadata>{metadata}</metadata><rect width="100%" height="100%" fill="#fffffe"/>'
             '<g font-family="Yu Gothic,Segoe UI,sans-serif">'+''.join(self.elements)+'</g></svg>\n')
        (OUT/'overview.svg').write_text(svg,encoding='utf-8',newline='\n')


def diagonal_witnesses():
    result=[]
    for mode in ('radius','outer'):
        for direction in (1,3,5,7):
            form=nucleus(0,PITCH,LARGE,None,direction,mode=mode)
            geometry_check(form['shapes'],form['paths'])
            result.append(dict(mode=mode,direction=direction,shapes=form['shapes'],paths=form['paths']))
    return result


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    data=specimens()
    normal=data['entries'][:6];kant=data['entries'][6:9];einstein=data['entries'][9:]
    col_width=806;full_width=1660
    normal_heights=[max(len(pack_lines(e['compiled'],col_width,SCALE)) for e in normal[i:i+2])*66+66 for i in range(0,6,2)]
    kant_heights=[len(pack_lines(e['compiled'],full_width,SCALE))*66+42 for e in kant]
    einstein_heights=[len(pack_lines(e['compiled'],full_width,SCALE))*66+53 for e in einstein]
    height=190+sum(normal_heights)+170+sum(kant_heights)+82+sum(einstein_heights)+245
    sheet=Sheet(1800,height)
    sheet.text(70,28,'NOEMA  /  BALANCED SCRIPT  /  09',17,ACCENT,False)
    sheet.text(68,66,'通常文・カント・アインシュタインの表記一覧',30)
    sheet.text(70,114,'半径線・中心で止まる接続・中心に線を入れない円を併用。空いている縦方向は、ごく一部でまとめて使う。',19,MUTED)
    sheet.text(70,156,'通常文',22,ACCENT)
    y=198
    for row_index,i in enumerate(range(0,6,2)):
        for column,entry in enumerate(normal[i:i+2]):
            x=70+column*854
            sheet.text(x,y,f'{i+column+1:02}  '+entry['label'],20)
            sheet.writing(entry,x,y+50,col_width)
        y+=normal_heights[row_index]
    y+=14
    sheet.text(70,y,'KANT  /  1784  /  第四段落第一文',22,ACCENT)
    sheet.text(70,y+42,data['kant_quote'],19,jp=False)
    sheet.text(70,y+80,'公衆の自己啓蒙は、個人の場合より可能である。自由を残せば、それはほとんど避けがたい。〔参考訳〕',20)
    sheet.text(70,y+116,'①②が一文に対応する形式記述。③は②の参照先を展開した補助表示で、原文の追加部分ではない。',18,MUTED)
    y+=160
    for entry,block_height in zip(kant,kant_heights):
        sheet.text(70,y,entry['label'],18,MUTED)
        sheet.writing(entry,70,y+35,full_width)
        y+=block_height
    y+=16
    sheet.text(70,y,'EINSTEIN  /  1905  /  同期条件と縦座標変換',22,ACCENT)
    y+=57
    for index,(entry,block_height) in enumerate(zip(einstein,einstein_heights)):
        sheet.text(70,y,f'原刊{entry["page"]}頁',20)
        sheet.formula(230,y-6,index)
        sheet.writing(entry,70,y+44,full_width)
        y+=block_height
    y+=16
    sheet.text(70,y,'大円の斜線：生成可能な八種類の確認（例文ではない）',18,MUTED)
    data['diagonal_witnesses']=diagonal_witnesses()
    for i,form in enumerate(data['diagonal_witnesses']):
        x=300+(i%4)*120+(0 if i<4 else 800)
        if i in (0,4):sheet.text(70 if i==0 else 870,y+50,'中心から' if i==0 else '円周から',18,MUTED)
        sheet.shape(form['shapes'],x,y+48)
        form['display']=dict(x=x,y=y+48)
    y+=140
    sheet.text(70,y,'円周から曲がるまで罫線間隔の1/2、無関係な構造との間には1/3を確保。意味と前後の配置から決定的に生成。',18,MUTED)
    sheet.text(70,y+32,'辞書・元の構文・配置対応は付属JSON/SVGへ保存。定義の全展開や画像だけの復号を保証するものではない。',18,MUTED)
    assert y+62<=height,(y,height)
    data['sheet']=dict(width=1800,height=height,scale=SCALE,guide_color=GUIDE,
                       rows=[len(pack_lines(e['compiled'],col_width if e['section']=='normal' else full_width,SCALE)) for e in data['entries']])
    sheet.save(data)
    (OUT/'specimens.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def build_report():
    data=specimens()
    inputs=[SOURCE,KANT,'scripts/balanced_circle_script.py','scripts/proof_balanced_circle_script.py','scripts/branch_circle_script.py',
            'scripts/circle_contact_script.py','scripts/proof_circle_contact_papers.py',
            'data/public-first-sentence-reading-v1.json','data/einstein-light-roundtrip-definition-source-reading-v1.json',
            'data/einstein-final-transform-source-reading-v1.json','concept/alphabet-concept.md','concept/noema-alphabet-concept.png',
            'tests/test_balanced_circle_script.py','docs/balanced-circle-script-v9.md']
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    return dict(version=VERSION,minimum_radial_run=MIN_RUN,minimum_radial_run_pixels=MIN_RUN*SCALE,
                minimum_separation=MIN_GAP,minimum_separation_pixels=MIN_GAP*SCALE,
                ray_directions_used=sorted({g['ray'] for e in data['entries'] for g in e['compiled']['groups'] if g['ray'] is not None}),
                stroke_modes=dict(Counter(g['stroke_mode'] for e in data['entries'] for g in e['compiled']['groups'])),
                pair_modes=dict(Counter(str(g['pair']) for e in data['entries'] for g in e['compiled']['groups'])),
                column_comparison=layout_comparison(),
                diagonal_capabilities=[dict(mode=f['mode'],direction=f['direction']) for f in diagonal_witnesses()],
                source_sha256={p:digest(ROOT/p) for p in inputs},
                output_sha256={str((OUT/p).relative_to(ROOT)).replace('\\','/'):digest(OUT/p) for p in ('overview.png','overview.svg','specimens.json')},
                entries=[dict(section=e['section'],groups=len(e['compiled']['groups']),dictionary=len(e['compiled']['dictionary']),
                              fused_occurrences=sum(len(g['fused_paths'])+sum(len(s['fused_paths']) for s in g['satellites']) for g in e['compiled']['groups'])) for e in data['entries']],
                limits=['Rendering preserves source syntax and scoped definition references; it does not unfold all lexical definitions.',
                        'Optical decoding, aesthetic acceptance and a complete script specification remain unverified.'])


if __name__=='__main__':
    prepare()
    print(json.dumps(build_report(),ensure_ascii=False,indent=2))
