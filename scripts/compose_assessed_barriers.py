"""Bind model-relative barriers to assessed inability and fixed liberty regimes."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_apparent_liberty import ROOT,SOURCE as PARENT,TRUE
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_restricted_utterance import primitive
from scripts.compose_qualified_utterance import closure

LIBRARY='examples/v016/assessed-barriers.noema'
SOURCE='examples/v016/kant-assessed-barriers.noema'
CORE='examples/v016/assessed-barriers-core.noema'
BASIS='data/assessed-barriers-basis-v1.json'
STATE='h[a] c';EQUATIONS='h[a '+STATE+'] c';FALSE=op('u',TRUE)
FIELDS=[('person','a'),('goal','e'),('variables','j[a]'),('equations',EQUATIONS),('factor','a'),('scene','h['+STATE+'] d'),
    ('available','h[a a d] c'),('prospects','h[a a d d] c'),('evaluated','h[a a d d] c')]
ACTUAL=FIELDS+[('anchor','d'),('observed',STATE)]
def params(fields):return ' '.join(n+' '+t for n,t in fields)
def av(fields):return [v(n) for n,t in fields]
def mask(factor):return 'i[variable a]['+op('e',v('variable'),factor)+']'
def fixed(flag):return 'i[variable a]['+(TRUE if flag else FALSE)+']'


def definitions():
    def ability(name,state):return k(name,v('person'),v('goal'),app(v('scene'),state),*[v(n) for n in ('available','prospects','evaluated')])
    text=definition('rww',params(FIELDS),both(k('rz',v('variables'),v('factor')),
        k('rv',v('variables'),v('equations'),mask(v('factor')),fixed(False),'i[state '+STATE+']['+ability('xd',v('state'))+']'),
        k('rw',v('variables'),v('equations'),mask(v('factor')),fixed(True),'i[state '+STATE+']['+ability('xg',v('state'))+']')))
    text+=definition('rwx',params(ACTUAL),both(k('rww',*av(FIELDS)),
        k('ru',v('variables'),v('equations'),fixed(False),fixed(False),v('observed')),
        app(v('observed'),v('factor')),op('e',app(v('scene'),v('observed')),v('anchor')),
        k('xg',v('person'),v('goal'),v('anchor'),*[v(n) for n in ('available','prospects','evaluated')])))
    return text


def additions():
    providers=[('variables','h[] j[a]'),('equations',EQUATIONS),('factor','h[] a'),('view','h['+STATE+'] d'),
        ('observed','h[d] '+STATE),('targets','h[a a] c')]
    text=''.join(primitive('iad'+n,t) for n,t in providers)+'r iadreport[a a i d[e] a d] c.'
    selected=app(v('state'),k('iadfactor'))
    expected='i[person a activity a context d]['+op('x',both(selected,k('iachighercivil',v('person'),v('activity'),v('anchor'))),
        both(op('u',selected),k('iaclowercivil',v('person'),v('activity'),v('anchor'))))+']'
    mapped='i[person a activity a context d]['+k('iachighercivil',v('person'),v('activity'),k('iadview',v('state')))+']'
    text+=definition('iadmatch','state '+STATE+' anchor d',both(
        k('rwu','p iacpeople','p iaccivilactivities',expected,mapped,v('anchor')),
        k('rwu','p iacpeople','p iaccivilactivities',mapped,expected,v('anchor'))))
    text+=definition('iadaligned','anchor d',both(
        k('hze','b view[k iaccivilgain[v view]]',k('iadvariables'),'p iadequations',k('iadfactor'),'p iadview'),
        *[k('rw',k('iadvariables'),'p iadequations',mask(k('iadfactor')),fixed(flag),
            'i[state '+STATE+'][k iadmatch[v state v anchor]]') for flag in (False,True)]))
    args=[v('person'),k('iacgoal',v('person'),v('activity')),k('iadvariables'),'p iadequations',k('iadfactor'),
        'i[state '+STATE+'][k iachigher[k iadview[v state]]]','p iacavailable','p iacprospects','p iacevaluated',
        k('iachigher',v('anchor')),k('iadobserved',v('anchor'))]
    text+=definition('iadbarrier','person a activity a anchor d',k('rwx',*args))
    target=k('iadtargets',v('person'),v('activity'))
    selected_scope=both(k('iacpeople',v('person')),k('iacmentalactivities',v('person'),v('activity')),
        k('iadbarrier',v('person'),v('activity'),v('anchor')))
    text+=definition('iadboundaries','anchor d',both(k('iadaligned',v('anchor')),
        op('e',k('iadview',k('iadobserved',v('anchor'))),v('anchor')),
        quant('g','person','a',quant('g','activity','a',target)),
        quant('f','person','a',quant('f','activity','a',op('y',target,selected_scope)))))
    text+=definition('iadcontrast','','b anchor['+both(op('t',k('iacappearance'),v('anchor')),k('iadboundaries',v('anchor')))+']','e')
    text+=definition('iadattribution','',k('iadreport',k('iacnode'),k('wa'),'r d[k iadcontrast[]]',k('iacscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib=deepcopy(parent);lib['declarations']=closure(parent,['rz','ru','rv','rw','xd','xg']);lib['statements']=[]
    lib=parse(format_graph(lib,'compact')+definitions())
    doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k iadattribution[]].')
    doc['statements']=parent['statements'][:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='assessed_model_relative_barriers_and_apparent_advantage',parent=PARENT,document=SOURCE,
        definitions={
            'rww':'同じ変数列・方程式・要因・本人・目標を保持する。要因を偽へ固定した解にxdの達成方法があり、真へ固定した非空の全解でxgの評価済みの達成不能がある。',
            'rwx':'rwwに加え、観測割当てが介入前の方程式を満たし、要因が真で、対応する状況が指定の現状と一致し、その現状で同じ目標がxgを満たす。',
            'iadmatch':'同じ人・市民的活動の範囲で、解に対応する許可選択肢が、要因が真なら現在の高い側、偽なら現在の低い側と両方向の包含で一致する。',
            'iadaligned':'両介入の全解で、要因の真偽と実際のiaccivilgainが対応し、iadmatchも成立する。名前だけの自由変数を認めない。',
            'iadbarrier':'前段と同じ本人・精神的活動の目標・方法・評価結果をrwxへ結び、別目標の達成不能を流用しない。',
            'iadboundaries':'非空の指定された境界対象全てが同じ人・精神的活動の範囲に入り、iadbarrierを満たす。観測割当ての比較視点も現在と一致する。全ての精神的活動が不可能だとはしない。',
            'iadcontrast':'前段の見かけの優位iacappearanceと、同じ基準視点のiadboundariesを合わせた内容。',
            'iadattribution':'結合した候補内容を同じ著者・本文箇所・範囲・文脈へ帰属する。'},
        inputs={
            'equations':'二値の構造方程式。変数列の範囲、背景、機構を介入の両側で固定する。現実への適合は別の仮定。',
            'view':'各割当てを前段の同じ二制度条件の比較視点に対応させる。iadmatchとhzeで自由の条件を照合する。',
            'observed':'現在の比較視点の観測割当て。元の方程式への適合を検査し、都合のよい介入後の解を現実として補わない。',
            'targets':'越えられない境界として選ぶ本人と精神的活動。許可範囲や全活動を勝手にこの範囲へ縮めない。'},
        limitations=[
            '明示した二値モデル内の強い因果的読みであり、原文の唯一の解釈や実社会の因果機構の同定ではない。変数・方程式・状況対応の適合は未確認。',
            '達成不能は利用可能な全方法の評価が整合し、指定結果で目標を達成する方法がないというxgに相対的である。無期限・全世界・未知の方法にわたる絶対的不可能ではない。',
            '原文の自由・精神的活動・度合いの語義と前段の包含尺度の適合は未完。両側で許可集合を一致させても、制度の全特徴や物理的背景の一致を自動では証明しない。',
            'dochの期待への反対、一般化の程度、より少ない自由による後続の展開、段落の全論証は未完。',
            '全保持者の規範変更や国家としての成立をこの節に補わない。前段の候補の同じ人口・活動・目標を用い、語義全体の完成とは扱わない。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
