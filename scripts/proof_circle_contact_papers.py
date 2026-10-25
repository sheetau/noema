"""Source quotations and explicit mathematical syntax specimens for draft 03.

Long prose is quoted, not falsely presented as completely rendered by the
currently limited geometric compiler. Mathematical expression trees are explicit
display interpretations, with original source and native definitions retained.
"""
import json
from pathlib import Path
from PIL import ImageFont

from scripts.circle_contact_script import Composer, SMALL, MEDIUM, LARGE, geometry_check, svg, VERSION

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/alphabet-circle-v3'
SYNCHRONY='data/einstein-light-roundtrip-definition-source-reading-v1.json'
TRANSFORM='data/einstein-final-transform-source-reading-v1.json'
KANT='data/public-first-sentence-reading-v1.json'


def ref(identity):
    return dict(kind='reference',identity=identity)


def op(kind,*arguments):
    return dict(kind=kind,arguments=list(arguments))


def paper_data():
    read=lambda p:json.loads((ROOT/p).read_text(encoding='utf-8'))
    synchrony,transform,kant=read(SYNCHRONY),read(TRANSFORM),read(KANT)
    light=synchrony['segments'][0]['text']
    for term in synchrony['segments'][0]['math']:
        light=light.replace('['+term['id']+']',term['printed'])
    # Names stand for semantic quantities, never the ASCII/Greek spelling.
    quantities={
        'departure':dict(label='t_A',radii=[SMALL],y=0,reading='A時計による出発時刻',native='eisjo'),
        'reflection':dict(label='t_B',radii=[MEDIUM],y=32,reading='B時計による反射時刻',native='eisjp'),
        'return':dict(label='t′_A',radii=[SMALL],y=64,reading='同じA時計による帰着時刻',native='eisjq'),
        'moving_coordinate':dict(label='ξ',radii=[SMALL,MEDIUM],y=0,reading='運動系の縦座標'),
        'factor':dict(label='β',radii=[SMALL,MEDIUM],y=32,reading='原文の正の変換係数β'),
        'rest_coordinate':dict(label='x',radii=[MEDIUM],y=0,reading='静止系の縦座標'),
        'velocity':dict(label='v',radii=[SMALL],y=32,reading='系の相対速度'),
        'time':dict(label='t',radii=[MEDIUM],y=64,reading='静止系の時刻'),
    }
    equations=[
        dict(source=SYNCHRONY,unit='einstein-1905:u0014',math_id='M0030',page='894',
             printed=synchrony['segments'][1]['math'][0]['printed'],
             expression=op('equal',op('subtract',ref('reflection'),ref('departure')),
                           op('subtract',ref('return'),ref('reflection'))),
             interpretation='三つの読取りを有効な実数とする。二度のt_Bは同じ反射時刻。同期の定義条件として引用する。'),
        dict(source=TRANSFORM,unit='einstein-1905:u0106',math_id='M0189',page='902',
             printed=transform['segments'][1]['math'][0]['reading'].split('; ')[1],
             expression=op('equal',ref('moving_coordinate'),op('multiply',ref('factor'),
                           op('subtract',ref('rest_coordinate'),op('multiply',ref('velocity'),ref('time'))))),
             interpretation='四つの変換式のうち縦座標の一式を引用。βは原文の係数で、現代の速度比βへ読み替えない。'),
    ]
    einstein=(ROOT/'examples/v014/einstein-reviewed-complete-v1.noema').read_text(encoding='utf-8').splitlines()
    native_math=[next(line for line in einstein if line.startswith('d '+name+'[')) for name in ('eimi','eims')]
    kant_lines=(ROOT/'examples/v016/kant-reviewed-complete-v1.noema').read_text(encoding='utf-8').splitlines()
    native_kant=['s[k r2lg[]].','s[k r2lo[]].']
    if not all(line in kant_lines for line in native_kant):
        raise ValueError('Selected Kant assertions no longer match the active manuscript')
    return dict(quantities=quantities,equations=equations,
                native_math=native_math,
                kant=dict(source=KANT,unit=kant['source']['unit'],text=kant['source']['text'],
                          native_assertions=native_kant,
                          rendering='original quotation and existing Noema text; full geometric prose rendering is not implemented'),
                light=dict(source=SYNCHRONY,unit=synchrony['segments'][0]['unit'],text=light),
                limits=['Math trees are explicit display interpretations, not a new native language definition or a full automatic translation.',
                        'Long prose is quoted in the original, with native text references; it is not replaced by opaque sentence glyphs.'])


def math_contour(expression,quantities):
    composer=Composer()
    def build(node,depth=0):
        if node['kind']=='reference':
            q=quantities[node['identity']]
            return composer.add(q['radii'],q['y'],'quantity',identity=node['identity'])
        kind=node['kind']
        # Operators act on operand contacts. Paired scope contacts delimit a
        # nested product/difference; equality has a shared middle nucleus.
        if kind=='equal':
            build(node['arguments'][0],depth+1)
            composer.add([LARGE],32,'equation',link='scope')
            build(node['arguments'][1],depth+1)
        elif kind in ('subtract','multiply'):
            entry=composer.add([SMALL],0 if depth%2 else 64,'math_scope',link='scope',operator=kind,side='entry')
            build(node['arguments'][0],depth+1)
            start_second=len(composer.nodes)
            build(node['arguments'][1],depth+1)
            composer.links[start_second-1].update(start='center' if kind=='subtract' else 'rim',end='rim',relation=kind)
            composer.add([SMALL],64 if depth%2 else 0,'math_scope',link='scope',operator=kind,side='exit',
                         end='center' if kind=='multiply' else 'rim')
            composer.nodes[entry]['scope_end']=len(composer.nodes)-1
        else:
            raise ValueError('Unsupported mathematical constructor: '+kind)
    build(expression)
    answer=composer.layout()
    answer['expression']=expression
    return answer


def typeset_formula(sheet,x,y,index):
    """Typeset source subscripts/primes without adding a plotting dependency."""
    from scripts.proof_circle_contact_script import SS, INK
    italic=ImageFont.truetype('C:/Windows/Fonts/timesi.ttf',44*SS)
    roman=ImageFont.truetype('C:/Windows/Fonts/times.ttf',44*SS)
    small=ImageFont.truetype('C:/Windows/Fonts/times.ttf',26*SS)
    baseline=(y+44)*SS
    cursor=x*SS
    if index:
        sheet.draw.text((cursor,baseline),'ξ = β(x − vt)',font=italic,fill=INK,anchor='ls')
        return
    tokens=[('B',False),' − ',('A',False),' = ',('A',True),' − ',('B',False)]
    for token in tokens:
        if isinstance(token,str):
            sheet.draw.text((cursor,baseline),token,font=roman,fill=INK,anchor='ls')
            cursor+=sheet.draw.textlength(token,font=roman)
        else:
            subscript,prime=token
            sheet.draw.text((cursor,baseline),'t',font=italic,fill=INK,anchor='ls')
            cursor+=sheet.draw.textlength('t',font=italic)+SS
            sheet.draw.text((cursor,baseline+11*SS),subscript,font=small,fill=INK,anchor='ls')
            if prime:sheet.draw.text((cursor,baseline-6*SS),'′',font=roman,fill=INK,anchor='ls')
            cursor+=max(sheet.draw.textlength(subscript,font=small),sheet.draw.textlength('′',font=roman) if prime else 0)+3*SS


def prepare():
    from scripts.proof_circle_contact_script import Sheet, CAPTIONS, MUTED, ACCENT
    OUT.mkdir(parents=True,exist_ok=True)
    data=paper_data()
    contours=[math_contour(e['expression'],data['quantities']) for e in data['equations']]
    sheet=Sheet(1800,1210)
    sheet.text(76,40,'NOEMA  /  EINSTEIN 1905  /  SOURCE EQUATIONS',18,ACCENT,False)
    sheet.text(72,90,'原文の数式を、演算と参照から組み立てる。',34)
    sheet.text(76,149,'同じ配置規則を適用。変数の綴りを文字ごとの円へ置換しない。',21,MUTED)
    for i,(equation,contour) in enumerate(zip(data['equations'],contours)):
        y=230+i*425
        sheet.text(76,y,f'原刊 {equation["page"]}頁  /  {equation["math_id"]}',20,ACCENT)
        typeset_formula(sheet,76,y+44,i)
        scale=min(1.5,1630/contour['width'])
        sheet.shape(contour['shapes'],70,y+157,scale)
        sheet.text(76,y+305,equation['interpretation'],20,MUTED)
        sheet.rule((76,y+367),(1724,y+367))
    sheet.text(76,1090,'円は量の種類と演算のまとまり、接続は演算の順序と範囲を表す。この数式部分の明示的な表示用解釈。',20,MUTED)
    sheet.text(76,1132,'M0030は既存定義eimi・eimsと三つの読取りを照合。M0189は校合記録の縦座標式を選択。',20,MUTED)
    sheet.save('paper-equations.png')

    sheet=Sheet(1800,1490)
    sheet.text(76,40,'NOEMA  /  ORIGINAL QUOTATIONS',18,ACCENT,False)
    sheet.text(72,90,'長めの原文と、既存記述の対応',34)
    sheet.text(76,165,'KANT  /  1784  /  原刊483頁',23,ACCENT)
    sheet.text(76,220,'Daß aber ein Publikum sich selbst aufkläre, ist eher möglich;',27,jp=False)
    sheet.text(76,265,'ja es ist, wenn man ihm nur Freiheit läßt, beinahe unausbleiblich.',27,jp=False)
    sheet.text(76,342,'公衆が自ら啓蒙することは、より可能である。しかも自由さえ残しておけば、',24)
    sheet.text(76,383,'それはほとんど避けがたい。〔既存の採用解釈に沿う参考訳〕',24)
    sheet.text(76,457,'対応する既存Noema： s[k r2lg[]].   s[k r2lo[]].',23)
    sheet.text(76,505,'「ほぼ」の留保、個人との比較、aber・ja・nurの提示関係も既存記述に含まれる。',21,MUTED)
    sheet.text(76,546,'この長文は原文引用と対応の掲載。量化・引用・高階適用を含む全文の新書記化は未実装。',21,MUTED)
    sheet.rule((76,605),(1724,605))
    sheet.text(76,650,'EINSTEIN  /  1905  /  原刊894頁',23,ACCENT)
    # Word wrapping preserves the complete source string; line breaks are only typography.
    words=data['light']['text'].split()
    lines=[];current=''
    for word in words:
        if len(current)+len(word)>100:
            lines.append(current);current=word
        else:current=(current+' '+word).strip()
    if current:lines.append(current)
    for i,text in enumerate(lines):sheet.text(76,712+i*42,text,25,jp=False)
    y=740+len(lines)*42
    sheet.text(76,y,'光がAからBへ進み、Bで反射され、Aへ戻る仮想設定。続く同期条件がM0030。',23)
    sheet.text(76,y+55,'原文の接続法・定義上の条件を保持し、実測済みの出来事や等式の事実成立へ置き換えない。',21,MUTED)
    sheet.rule((76,1265),(1724,1265))
    sheet.text(76,1310,'出典：保存済みの原刊校合・読解記録。引用文と数式の記録はpaper-specimens.jsonに保存。',21,MUTED)
    sheet.text(76,1355,'新しい原始概念を一文につき一つ追加して、長文を描けたことにする処理は行っていない。',21,MUTED)
    sheet.save('paper-quotations.png')
    data['contours']=contours
    (OUT/'paper-specimens.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    wrapped=dict(version=VERSION,source={'quotation_sources':[SYNCHRONY,TRANSFORM]},profile=data['quantities'],sentences=contours)
    for i in range(len(contours)):
        (OUT/f'paper-equation-{i+1:02}.svg').write_text(svg(wrapped,i),encoding='utf-8',newline='\n')
    return data
