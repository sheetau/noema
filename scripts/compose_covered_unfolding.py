"""Bind a latent-to-manifest change to one process, object and persistent cover."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_ordered_contrast import ROOT,SOURCE as PARENT
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive

LIBRARY='examples/v016/covered-unfolding.noema'
SOURCE='examples/v016/kant-covered-unfolding.noema'
CORE='examples/v016/covered-unfolding-core.noema'
BASIS='data/covered-unfolding-basis-v1.json'
DESCRIPTION='i[h[a] e]'
FIELDS=[('object','a'),('process','a'),('start','d'),('end','d'),('history','h[d] c'),('before','h[d d] c'),
    ('transitions','h[a d d] c'),('affected','h[a a d d] c'),('features','h[a] c'),
    ('latent','h[a a d] c'),('manifest','h[a a d] c')]
COVER=[('cover','a'),('surrounds','h[a a d] c'),('resistant','h[a d] c')]
def params(fields):return ' '.join(n+' '+t for n,t in fields)
def args(fields):return [v(n) for n,t in fields]


def definitions():
    feature=app(v('features'),v('feature'))
    end=app(v('manifest'),v('object'),v('feature'),v('end'))
    initial=app(v('manifest'),v('object'),v('feature'),v('start'))
    text=definition('rw4',params(FIELDS),both(
        k('tg',*[v(n) for n in ('history','before','process','start','end','transitions')]),
        app(v('affected'),v('process'),v('object'),v('start'),v('end')),
        quant('g','feature','a',both(feature,op('u',initial))),
        quant('f','feature','a',op('y',feature,both(app(v('latent'),v('object'),v('feature'),v('start')),end)))))
    interval=both(app(v('history'),v('point')),
        op('x',op('e',v('point'),v('start')),app(v('before'),v('start'),v('point'))),
        op('x',op('e',v('point'),v('end')),app(v('before'),v('point'),v('end'))))
    text+=definition('rw5',params(FIELDS+COVER),both(k('rw4',*args(FIELDS)),op('u',op('e',v('cover'),v('object'))),
        quant('f','point','d',op('y',interval,both(
            app(v('surrounds'),v('cover'),v('object'),v('point')),app(v('resistant'),v('cover'),v('point')))))))
    return text


def additions():
    providers=[('history','h[a d d] c'),('before','h[a d d d] c'),('features','h[a d a] c')]
    providers += [(n,t) for n,t in FIELDS[6:] if n!='features']+COVER[1:]
    text=''.join(primitive('iag'+n,t) for n,t in providers)
    text+='r iagnode[] a.r iagscope[] a.'
    references=dict(object=v('object'),process=v('process'),start=v('start'),end=v('anchor'),
        history='i[point d][k iaghistory[v object v anchor v point]]',
        before='i[left d right d][k iagbefore[v object v anchor v left v right]]',
        features='i[feature a][k iagfeatures[v object v anchor v feature]]',cover=v('cover'))
    references.update({n:'p iag'+n for n,t in FIELDS[6:]+COVER[1:] if n!='features'})
    unfolded=k('rw5',*[references[n] for n,t in FIELDS+COVER])
    text+=definition('iagdepiction','object a','b anchor['+quant('g','process','a',quant('g','start','d',quant('g','cover','a',both(
        unfolded,k('df',v('process'),k('qb'),v('anchor')),k('dg',v('process'),v('anchor'))))))+']','e')
    text+=definition('iagframe','target '+DESCRIPTION,k('qh',k('iagnode'),k('wa'),v('target'),'r[p iagdepiction]',k('wh')))
    # The intended Hang/Beruf reading is deliberately still an explicit argument.
    # Quoting this template does not assert the antecedent, the literal depiction,
    # or the existence of a human-like agent called Nature.
    text+='r iagreport[a a i b[h['+DESCRIPTION+'] c] a d] c.'
    text+=definition('iagattribution','',k('iagreport',k('iagnode'),k('wa'),'r b[p iagframe]',k('iagscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib=deepcopy(parent);lib['statements']=[];lib['declarations']=closure(parent,['tg'])
    lib=parse(format_graph(lib,'compact')+definitions())
    doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k iagattribution[]].')
    doc['statements']=parent['statements']+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='partial_depiction_template_not_completed_germ_translation',parent=PARENT,document=SOURCE,
        definitions={
            'rw4':'同じ順序付き履歴の前後を同じ変化過程が結び、同じ対象がその過程の影響を受ける。固定した非空の性質範囲は開始時に潜在し、終了時に全て顕在化している。そのうち少なくとも一つは開始時にはまだ顕在化していない。',
            'rw5':'rw4に加え、対象と異なる同じ覆いが開始から終了までの履歴内の全状況で対象を包み、変形への抵抗を持つ。対象・覆いを途中で別物へ置き換えない。',
            'iagdepiction':'同じ対象・基準視点で固定した履歴と性質範囲について、基準視点を終了点とするrw5の過程がある。描写の内部で自然qbをその過程の行為者へ結び、過程が終了時点で生起する。',
            'iagframe':'明示的な対象側の性質記述を、iagdepictionによる非字義的な描写へqhで対応させるひな形。対象側の引数は未充足である。',
            'iagattribution':'ひな形の階数1の記述を、本文箇所・著者・範囲・文脈へ部分注記として帰属する。条件文の前件や描写を現在の事実として実行しない。'},
        inputs={
            'latent':'同じ対象にその性質を顕在化させる内在的な構成・素質がある。単なる論理的可能性、他の対象の性質、現在の発現の有無とは区別する。素質の機構は入力として残る。',
            'manifest':'同じ対象に、その性質がその時点で実際に発現している。観測者が知っていることだけで置き換えない。',
            'features':'その展開を記述する性質の範囲。終了時に成功した性質だけを選ばず、同じ対象と比較文脈で固定する。',
            'affected':'その過程が同じ二端点の間で同じ対象の変化に関わる。二時点の前後関係だけから因果機構を証明しない。',
            'surrounds/resistant':'同じ覆いが対象を物理的に包むことと、変形への抵抗。制度上の保護や禁止を字義的条件へ直接代入しない。硬さの尺度・閾値・材料機構の一般定義は残る。',
            'history/before':'対象と基準視点で固定した履歴とその厳密な全順序。有限の診断例が現実の全時点を尽くした証明ではない。'},
        limitations=[
            '性質の潜在から顕在への展開という操作的な候補であり、Keimの植物学的な分類や起源、自然の一般的な意味は未定義。種子そのものや胚の分類へ固定しない。',
            '対象側のHangとBeruf、自由な思考、その発展の語義は未充足。今回のひな形をそれらの完成した定義とは扱わない。',
            '初期に一部が発現済みでもよい。全性質の単調な発達、失敗や一時的な後退の不在、終了後の永続や他の性質の改善は要求しない。',
            '覆いは終了時点でも残る。破裂、除去、外への脱出や、包むことが成長の原因であることを補わない。',
            '自然の行為者としての提示は比喩の内部だけに置く。自然の意識や人間性、当該過程の現実の発生を断言しない。',
            'am zartlichstenの世話、潜在的性質と芽の起源、覆いと制度の対応、条件文の後件と因果的な波及、全文の意味確認は未完。原文の対応文字数を増やさない。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
