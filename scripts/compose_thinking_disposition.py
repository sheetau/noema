"""Compose graded nonfactive orientation and explicit alternatives for a calling."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_covered_unfolding import ROOT,SOURCE as PARENT,FIELDS as GROWTH
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive

LIBRARY='examples/v016/thinking-disposition.noema'
SOURCE='examples/v016/kant-thinking-disposition.noema'
CORE='examples/v016/thinking-disposition-core.noema'
BASIS='data/thinking-disposition-basis-v1.json'
CODE='i[h[a] e]';HIGH='i b[h[a] e]'
ZERO='n p a b';ONE='n p b b';TRUE='e['+ZERO+']['+ZERO+']';FALSE='u['+TRUE+']'
FIELDS=[('person','a'),('target',CODE),('anchor','d'),('points','j[d]'),('scope','h[a '+CODE+' d d] c'),
    ('classified','h[a '+CODE+' d d] c'),('weights','h[a '+CODE+' d d] b'),('orientation','h[a '+CODE+' d] c'),('threshold','b')]


def definitions():
    bind=lambda name:'i[point d]['+app(v(name),v('person'),v('target'),v('anchor'),v('point'))+']'
    weights=bind('weights')
    hits='i[point d]['+app(v('orientation'),v('person'),v('target'),v('point'))+']'
    total=k('rd4',v('points'),'i[point d]['+TRUE+']',weights)
    score=k('rd4',v('points'),hits,weights)
    text=definition('rw6',' '.join(n+' '+t for n,t in FIELDS),both(
        k('rd5',v('points'),bind('scope'),bind('classified'),weights),
        k('hc',ZERO,v('threshold')),op('u',k('hc',ONE,v('threshold'))),
        op('u',k('hc',score,k('hb',v('threshold'),total)))))
    text+=definition('rw7','node a author a target '+HIGH+' depiction '+HIGH+' context d presents h[a a '+HIGH+' '+HIGH+' d] c',both(
        op('u',op('e',v('target'),v('depiction'))),app(v('presents'),*[v(n) for n in ('node','author','target','depiction','context')])))
    return text


def additions():
    providers=[('points','h[a d] j[d]'),('scope','h[a '+CODE+' d d] c'),('classified','h[a '+CODE+' d d c] c'),
        ('weights','h[a '+CODE+' d d] b'),('favor','h[a '+CODE+' d] c'),('urge','h[a '+CODE+' d] c'),
        ('threshold','h[a '+CODE+' d c] b'),('assigned','h[a a '+CODE+' d] c'),('source','h[] a'),
        ('leanfeature','h[] a'),('callfeature','h[] a'),('history','h[a d d] c'),('before','h[a d d d] c'),
        ('transitions','h[a d d] c'),('affected','h[a a d d] c'),('latent','h[a a d] c'),
        ('presents','h[a a '+HIGH+' '+HIGH+' d] c')]
    text=''.join(primitive('iah'+n,t) for n,t in providers)
    text+=definition('iahthinking','person a','b point['+both(k('aa',v('person')),quant('g','judgment','a',
        k('rcr',v('person'),v('judgment'),v('point'),*[ 'p '+n for n in ('ab','ac','fa','fb','fc','fd','ad') ])))+']','e')
    bound='i[person a target '+CODE+' anchor d point d][k iahclassified[v person v target v anchor v point v impulse]]'
    attitude='i[person a target '+CODE+' point d]['+op('x',both(v('impulse'),k('iahurge',v('person'),v('target'),v('point'))),
        both(op('u',v('impulse')),k('iahfavor',v('person'),v('target'),v('point'))))+']'
    text+=definition('iahorientation','person a anchor d impulse c',k('rw6',v('person'),'r[p iahthinking]',v('anchor'),
        k('iahpoints',v('person'),v('anchor')),'p iahscope',bound,'p iahweights',attitude,
        k('iahthreshold',v('person'),'r[p iahthinking]',v('anchor'),v('impulse'))))
    islean=op('e',v('feature'),k('iahleanfeature'));iscall=op('e',v('feature'),k('iahcallfeature'))
    call=op('x',both(v('inner'),k('iahorientation',v('person'),v('point'),TRUE)),
        both(op('u',v('inner')),k('iahassigned',k('iahsource'),v('person'),'r[p iahthinking]',v('point'))))
    text+=definition('iahmanifest','person a feature a point d inner c',op('x',
        both(islean,k('iahorientation',v('person'),v('point'),FALSE)),both(iscall,call)))
    references=dict(object=v('person'),process=v('process'),start=v('start'),end=v('anchor'),
        history='i[point d][k iahhistory[v person v anchor v point]]',
        before='i[left d right d][k iahbefore[v person v anchor v left v right]]',
        transitions='p iahtransitions',affected='p iahaffected',
        features='i[feature a]['+op('x',islean,iscall)+']',latent='p iahlatent',
        manifest='i[person a feature a point d][k iahmanifest[v person v feature v point v inner]]')
    body=both(op('u',op('e',k('iahleanfeature'),k('iahcallfeature'))),
        quant('g','process','a',quant('g','start','d',k('rw4',*[references[n] for n,t in GROWTH]))))
    text+=definition('iahdevelopment','person a inner c','b anchor['+body+']','e')
    text+=definition('iahinner','person a',k('iahdevelopment',v('person'),TRUE),'e')
    text+=definition('iahvocation','person a',k('iahdevelopment',v('person'),FALSE),'e')
    selected=op('x',op('e',v('reading'),'r b[p iahinner]'),op('e',v('reading'),'r b[p iahvocation]'))
    text+=definition('iahfamily','reading '+HIGH,both(selected,k('rw7',k('iagnode'),k('wa'),v('reading'),
        'r b[p iagdepiction]',k('wh'),'p iahpresents')))
    text+='r iahreport[a a i c[h['+HIGH+'] c] a d] c.'
    text+=definition('iahattribution','',k('iahreport',k('iagnode'),k('wa'),'r c[p iahfamily]',k('iagscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib=deepcopy(parent);lib['statements']=[];lib['declarations']=closure(parent,['rd4','rd5'])
    lib=parse(format_graph(lib,'compact')+definitions())
    doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k iahattribution[]].')
    doc['statements']=parent['statements'][:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='two_explicit_development_readings_not_unique_translation',parent=PARENT,document=SOURCE,
        definitions={
            'rw6':'同じ本人・対象記述・基準文脈の評価機会を、重複なく完全に列挙する。全機会が分類済みで正の重みを持ち、志向が成立する重みの合計が、全重みと0より大きく1以下の閾値の積以上である。',
            'rw7':'階数1の異なる性質記述を、同じ箇所・著者・文脈の非字義的な提示へ結ぶ。両内容を実行しない。既存qhと同じ役割を、記述に向けた心理状態を含む性質にも用いる。',
            'iahthinking':'本人が人で、自分の理解力を使い、用いた理由に支持され、他人の指導によらない判断rcrがあるという内容。',
            'iahorientation':'同じiahthinkingの記述と同じ本人をrw6へ結ぶ。肯定的な志向と内的な衝動を別入力にし、それぞれの分類済み条件と閾値を使う。',
            'iahmanifest':'第一の性質は自由な思考への志向。第二は、innerが真なら同じ思考への内的な衝動、偽なら明示した出所から本人への課題の付与。',
            'iahdevelopment':'二性質を区別し、既存rw4を用いて同じ人に潜在していた志向と呼びかけが顕在化する過程を記述する。精神的な過程と身体的な描写の過程を同一にしない。',
            'iahinner/iahvocation':'内的な衝動と、課題・義務としての呼びかけをそれぞれ採った二つの対象側の候補。どちらも実際の思考の実行や成功を要求しない。',
            'iahfamily':'候補をiahinnerかiahvocationに明示的に限定し、選んだ一つを前段のiagdepictionへ対応させる。両候補の同時成立も、どちらが正しいかも断言しない。',
            'iahattribution':'二つの候補を持つ閉じたひな形の階数2の記述を部分注記として帰属する。前段の未充足targetを、明示した候補へ具体化する。'},
        inputs={
            'scope/points/weights':'判断結果に合わせて変えない評価機会とその重要度。正の有理数重みを用いる有限評価であり、観測標本から一般的な性格や確率を推定しない。',
            'favor/urge':'その人が同じ記述に向ける肯定的な志向と、そこへ向けられる内的な衝動。実行、実行能力、義務、対象内容が真だという認識は別条件。心理機構の基礎説明は残る。',
            'classified/threshold':'志向と衝動をそれぞれ評価済みか、どれだけの重みを満たせばその程度として採るか。閾値を一律の数値や語の置換表へ固定しない。',
            'assigned/source':'指定の出所が同じ本人に同じ記述の活動を課題として位置付ける。実際の履行、正当性、法的な強制や職業の地位は自動的には含まない。出所を自然や神へ固定しない。',
            'latent/history/before/transitions/affected':'本人の同じ二性質の潜在性と顕在化の履歴・過程。前段のrw4の意味規約を引き継ぐ。'},
        limitations=[
            '自由な思考を独立した理由ある判断として読む候補であり、想像・疑問・探索を含む思考全体や自由の全語義を定義し終えたものではない。',
            'Hangの程度を、明示した評価機会での志向の重みの割合として読む操作的な候補。感情の強度そのもの、傾向の反事実的機構、現実の全機会の網羅性は未完。',
            'Berufの二候補は語義資料に沿って区別したが、原文での唯一の読みは未確定。列挙した候補が全ての可能な解釈を尽くすとはしない。',
            '心理的な対象への記述は引用し、現実の思考やその能力と区別する。同じ真偽の別記述への志向・課題付与の流用は認めない。',
            '潜在的な素質の起源、自然の世話、覆いと制度の対応、条件文の後件と社会への作用は未完。候補の接続だけで全文の意味一致や新しい文字範囲の対応を認定しない。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
