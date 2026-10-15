"""Bind plural permission and compliance to one quoted speaker and audience."""
import json
from copy import deepcopy
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,quant
from scripts.compose_situated_criticism import params
from scripts.compose_described_norms import RULE,DESCRIPTION
from scripts.compose_choice_permissions import LIBRARY as CHOICES,PC,MC
from scripts.compose_scoped_obedience import LIBRARY as OBEDIENCE
from scripts.compose_public_permission_risk import INPUTS

PARENT='examples/v016/kant-focused-permission.noema'
LIBRARY='examples/v016/shared-quotation.noema'
SOURCE='examples/v016/kant-shared-quotation.noema'
CORE='examples/v016/shared-quotation-core.noema'
BASIS='data/shared-quotation-basis-v1.json'
COMMON=[('source','a'),('anchor','d'),('people','h[a d] c')]
PERMISSION=COMMON+[(n,'h[a a d] '+t) for n,t in [('topics','c'),('extents','c'),('candidates','c'),('subject','a'),('extent','a'),('roles','a'),('targets',DESCRIPTION)]]+[('required',RULE),('allowed',RULE)]
OBEY=COMMON+[(n,'h[a a d] '+t) for n,t in [('rolescope','c'),('items','c'),('orderroles','a'),('actions','a'),('descriptions',DESCRIPTION),('signs','c')]]+[('required',RULE)]
FIELDS=PERMISSION+[f for f in OBEY if f[0] not in dict(PERMISSION)]
CODES=[(n,'i b['+t+']') for n,t in FIELDS]
SEQUENCE='j['+MC+']'
TEMPLATE='h[i b[a] i b[h[a d] c] i b[d]] '+SEQUENCE
FIELD_SYMBOLS={n:'hzsfield'+chr(ord('a')+i) for i,(n,_) in enumerate(INPUTS)}

def av(fields):return [v(n) for n,_ in fields]

def definitions():
    role='i[role a]['+app(v('rolescope'),v('person'),v('role'),v('anchor'))+']'
    selectors=['i[item a]['+app(v(n),v('person'),v('item'),v('anchor'))+']' for n in ('items','orderroles','actions','descriptions','signs')]
    perperson=k('rty',v('source'),v('person'),v('anchor'),role,*selectors,v('required'))
    text=definition('rua',params(OBEY),'b point['+quant('f','person','a',op('y',app(v('people'),v('person'),v('anchor')),op('t',perperson,v('point'))))+']','e')
    population='i[person a]['+app(v('people'),v('person'),v('anchor'))+']'
    policy=k('rtu',population,*[v(n) for n in ('topics','extents','candidates','subject','extent','anchor','source','roles','targets','required','allowed')])
    text+=definition('rub',params(PERMISSION),policy,'e')
    permission='o a[r b[p rub]]['+' '.join(av(PERMISSION))+']'
    obedience='o a[r b[p rua]]['+' '.join(av(OBEY))+']'
    text+=definition('ruc',params(CODES),k('rtv',permission,obedience),SEQUENCE)
    return text

def library():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=dict(parent,declarations=[],statements=[]);names={}
    for path in (CHOICES,OBEDIENCE):
        for declaration in parse((ROOT/path).read_text(encoding='utf-8'))['declarations']:
            name=declaration['name']
            if name in names:assert names[name]==declaration
            else:names[name]=declaration;doc['declarations'].append(declaration)
    return parse(format_graph(doc,'compact')+definitions())

def build():
    lib=library();doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements=doc['statements'];doc['statements']=[]
    names={d['name']:d for d in doc['declarations']}
    for declaration in lib['declarations']:
        if declaration['name'] in names:assert declaration==names[declaration['name']]
        else:doc['declarations'].append(declaration)
    text=''
    for name,t in INPUTS:text+='r '+FIELD_SYMBOLS[name]+'[a a d] '+t+'.'
    special={'source','anchor','people','subject','roles','targets','required','allowed'}
    for name,t in FIELDS:
        if name not in special:text+='r hzs'+name+'['+t[2:t.rfind(']')]+'] '+t[t.rfind(']')+1:].strip()+'.'
    for name,field in [('hzsroles','role'),('hzssubject','subject')]:
        text+=definition(name,'person a activity a anchor d','s['+k(FIELD_SYMBOLS[field],v('person'),v('activity'),v('anchor'))+']','a')
    text+=definition('hzstargets','person a activity a anchor d',k('rri',*[k(FIELD_SYMBOLS[n],v('person'),v('activity'),v('anchor')) for n,_ in INPUTS]),DESCRIPTION)
    refs={n:'r b[p hzs'+n+']' for n,_ in FIELDS};refs.update(source=v('speaker'),anchor=v('context'),people=v('audience'),required='r b[p h7a]',allowed='r b[p h7b]')
    text+=definition('hzsquotation','speaker i b[a] audience i b[h[a d] c] context i b[d]',k('ruc',*[refs[n] for n,_ in FIELDS]),SEQUENCE)
    text+='r hzsnode[] a.r hzsscope[] a.r hzsreport[a a i c['+TEMPLATE+'] a d] c.'
    text+=definition('hzsattribution','',k('hzsreport',k('hzsnode'),k('wa'),'r c[p hzsquotation]',k('hzsscope'),k('wh')))
    doc=parse(format_graph(doc,'compact')+text+'s[k hzsattribution[]].');doc['statements']=statements+doc['statements']
    lookup={d['name']:d for d in doc['declarations']};pending=_references(doc['statements'][-1:]);keep=set()
    while pending:
        name=pending.pop()
        if name in keep:continue
        keep.add(name);pending.update(_references(lookup[name])-keep)
    core=deepcopy(doc);core['declarations']=[d for d in doc['declarations'] if d['name'] in keep];core['statements']=doc['statements'][-1:]
    return {LIBRARY:format_graph(lib,'compact')+'\n',SOURCE:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n'}

def basis():
    return dict(status='partial_quoted_permission_and_plural_compliance_template',parent=PARENT,document=SOURCE,
        definitions={
            'rua':'同じ出所・基準文脈と聞き手範囲について、各本人の要求記録・役割範囲・履行をrtyへ接続する。別人の要求記録を流用しない。',
            'rub':'同じ基準文脈の聞き手範囲を選択許可rtuへ接続する。話題と程度の希望は各本人ごとに照合する。',
            'ruc':'同じ出所・基準文脈・聞き手範囲・要求関係の閉じた記述を、許可と服従の両内容へ渡す。一方だけ別の話者や聞き手に差し替える引数を持たない。',
            'hzsroles/hzssubject':'許可対象の行為を構成するのと同じ提示項目から、役割と話題の指示先を取り出す。',
            'hzstargets':'同じ本人・活動・基準文脈の提示項目から、公的提示と自分の理解力の使用を組み合わせた既存rriの行為記述を構成する。',
            'hzsquotation':'引用内の話者・聞き手・基準文脈を引数として残し、許可を述べる内容と履行を求める指令の列を構成する。特定の君主を固定せず、実際に発言したとは主張しない。',
            'hzsattribution':'著者がこの原文範囲に、指定した引用のひな形を提示していることを帰属する。引用の実行・許可の新設・服従の達成を要求しない。'},
        bindings={
            'hzsreport':'箇所・著者・引用ひな形の閉じた記述・原文範囲・文脈に関する引用提示の帰属。上位の発話可能条件の主張とは別。',
            'hzsnode/hzsscope':'第17区間の引用部分の位置と範囲。',
            'hzstopics/hzsextents':'同じ聞き手が同じ基準文脈で希望する話題・程度。',
            'hzscandidates/hzsextent':'活動候補と程度の分類。実行済みの行為に限定しない。',
            'hzsrolescope/hzsitems/hzsorderroles/hzsactions/hzsdescriptions/hzssigns':'各聞き手の同じ基準文脈における要求の役割範囲・記録・役割・活動・閉じた行為記述・極性。',
            'hzsfield*':'同じ本人・活動・基準文脈の公的提示項目。既存rriの構成に使う。'},
        unresolved=[
            '引用部分の明示した読解候補であり、誰だけがこれを言えるか、啓蒙・影への恐れ・軍隊・国家の条件はまだ帰属していない。',
            '論じる行為は本人の理解力の使用と自己帰属を伴う公的提示として部分的に読む。推論の内容・正当性やräsonnierenの全語義を確定しない。',
            '話題と程度の直積は選択した読みである。程度の測定・上限と行為の量の接続、望む範囲そのものの妥当性は未完。',
            'nurの限定・留保と二つの発話の談話関係は未記述で、今回の原文対応範囲から除く。許可の成否を服従の成否と同一視しない。',
            '服従側は指定要求への全面的適合を表す。意図・権威の正当性・制度上の役割の説明は未完。',
            '有限評価では全記述域への要求網羅性を列挙しない。限定した記述での診断を全域の証明とはしない。',
            '引用の話者・聞き手・文脈は閉じた記述として渡す。未指定の話者を現在の統治者として補わない。',
            '原文区間全体の意味一致、文化的・制度的な基礎概念の説明は未完。'])

def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))

if __name__=='__main__':main()
