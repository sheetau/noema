"""Bridge actual two-field answers to individual records in ordered problem series."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_limits import ROOT,v,call as k,app,op,both,quant as q
from scripts.compose_material_relative_frame import define,args
from scripts.compose_body_rest_field_method import SETTING,FIELD,REGION
from scripts.compose_field_equations import POINT

def read(path):return (ROOT/path).read_text(encoding='utf-8')
PARENT='examples/v014/einstein-body-rest-field-method.noema';PARENT_BASIS='data/body-rest-field-method-basis-v1.json'
FULL='examples/v014/einstein-field-answer-records.noema';CORE='examples/v014/field-answer-records-core.noema'
BASIS='data/field-answer-records-basis-v1.json';ANNOTATIONS='data/field-answer-records-identifiers-v1.json'
META=[(n,'a') for n in ('process','body','frame','lengthunit','timeunit','chargeunit','electricunit','magneticunit','forceunit')]+[('region',REGION),('context','d')]
CODEC=[('electricreader','h[a] '+FIELD),('magneticreader','h[a] '+FIELD),('encoder','h['+FIELD+' '+FIELD+'] a')]
PAIR=[('electric',FIELD),('magnetic',FIELD)]
QTYPE='g['+FIELD+' '+FIELD+']'
TASK=META+CODEC+[('question',QTYPE)]
FAMILY='h[a] g[a]'
METHOD=SETTING+CODEC
ATTACH=[('problem','a'),('questions',FAMILY),('recordquestion','g[a]')]
LINK=METHOD+[('problem','a'),('questions',FAMILY)]
SERIES=LINK+[('targets','j[a]'),('answers','j[a]'),('slot','b')]
PAYLOAD=[('record','a')]+META+PAIR
PRIMITIVES={'eisvj':(PAYLOAD,'recordという個体参照で扱う構造化した解答データが、指定された同じprocess・body・frame・長さ時間及び四物理単位・region・contextの欄と、型FIELDのelectric/magneticという二つの関数の欄を持つという記録内容の対応。物理的な実測文書に限らず数学的な解答データを含む。個体名や自然言語文字列が答えそのものという対応ではない。欄の一致だけで物理的な正解・実測済み・同じ方法での計算可能性を認定しない。未指定欄を任意の既定値で補わず、数値関数を暗黙に個体へ型変換しない。')}
MEANINGS={
 'ekv7':'同じrecordから同じ二つの型付きreaderで取り出した関数が、同じ全METAの記録内容eisvjに対応する。メタデータと二場の中身の一致を確認し、これだけで正解又は実測済みとしない。',
 'ekwa':'同じ記録内容ekv7を保ち、その同じ二つの関数を実際のNoema二場質問へ答えとして渡す。別の問題・系・物体・単位の記録や片方だけの答えを拒否する。',
 'ekwb':'同じMETA・reader・encoder・実際の二場質問を固定し、ekwaを満たす一つの個体記録を問うg[a]質問を構成する。二関数を個体名の文字列で代用しない。',
 'ekwc':'指定された同じ二場をencoderへ渡して得る個体記録がekv7を満たし、その二readerの三成分が元の二場と同じ領域全体でejs3により一致する。全個体役割での関数同一性や領域外の延長の一致を要求しない。',
 'ekwd':'実際の二場質問を満たす全ての関数対について、同じencoderの記録がekwcを満たし、その復号した二場も同じ質問を満たすekwaであると要求する。正解の一例だけを表現可能とせず、候補の存在自体は要求しない。全関数域を有限候補へ縮めない。',
 'ekwe':'同じproblemについてquestionsが与えるg[a]質問とrecordquestionとの答え集合が全個体記録で一致する。選んだ場の下位問題だけを対応させ、他の問題の質問を二場質問へ一括で置き換えない。',
 'ekwf':'同じSETTING25のekv5を、新系・同じ対象・単位・s6m逆像領域・文脈の記録へekwbで接続したg[a]質問。全物理設定とreader/encoderを候補の外側で固定する。',
 'ekwg':'同じ旧両場をs6k/s6lで変換した実際の二関数を同じencoderへ渡して得る個体記録。記録を構成することと、その物理的な正解及び記録内容の忠実性を分ける。',
 'ekwh':'同じ設定の物理的な変換ekv6、変換された実際の二場の記録内容及び全領域一致ekwc、同じekwfへのekwgの合致を結ぶ。さらに同じ正逆s46をeisqtで二系の原点・軸・時計を含む全座標規約へ結び、一つの出来事の偶然の一致で全系の対応を代用しない。',
 'ekwi':'同じ物理的な二場質問ekv5の全正解を表現できるekwdと、同じ変換の実際の記録化ekwhを結ぶ。一般の無関係な関数全てを個体へ単射で符号化する主張ではない。',
 'ekwj':'同じ場の下位問題と質問族への全記録での対応ekwe、同じ物理設定の忠実な記録化ekwi、実際の構成記録ekwgがその問題の質問を満たすことを共有する。質問族の他の問いは保持する。',
 'ekwk':'同じ有限targets/answers列の指定位置slotに同じ場の下位問題problemと実際の構成記録ekwgがあり、ekwj及び既存ekviの全位置の質問合致が成立する。列全体を単項へ固定せず、他の位置の問い・答え・順序・反復も保持する。',
}
LIMITS=[
 'u0226で使う二場の手続きと前回の問題列還元を接続する依存群。12定義と型付き解答記録の一般関係一つを追加する。原文の全光学問題を二場を問う下位問題だけへ縮めず、同じ質問族の一つの下位問題を列の任意位置へ接続する。既存406主張と判断を保存し、新しい原文単位はまだ意味確認済みとしない。',
 '個体参照の解答記録は構造化データであり、実数・関数を暗黙に個体化しない。eisvjと型付きreader/encoderの契約を別に示す。本文の自然言語文字列やリンクを答え内容の代用にしない。',
 '全てのFIELD関数を全個体役割で区別して個体に単射で符号化する要求は置かない。FIELDは個体を引数とするので、そのような全関数の完全符号化は一般に不適切である。三空間成分・指定領域のejs3による一致だけを記録化の内容同値とし、領域外や無関係な役割の延長を一致させない。',
 '表現の完全性ekwdは同じ実際の二場質問の全正解対を対象とする。復号後も同じ質問を満たすことを明示的に要求し、ejs3の数値一致だけから物理的な帰属述語や質問全体の不変性を推測しない。正解がなければ完全性だけが空虚に成立し得るが、ekwiには実際の変換正解ekwhも必要である。',
 'encoderは二つの関数からデータ個体を構成する入力関数で、存在するだけで実効的な計算手順だとは認定しない。後続の方法の手続き案への接続で実効性と採用する具体的な操作を結ぶ。',
 'eisqtは既存の一般的な物理座標対応を再利用する。正逆s46を同じ二系・ta/rb・文脈の原点・軸・時計・全域へ結ぶ。前段の出来事記録対の式だけから全座標規約を推定しない。',
 '同じ光への帰属、光学問題の全範囲、静止側の問題列から元の質問への再構成を含む実効的方法の手続き案、本質的役割、先行方法への参照、三文全体の著者提示と意味判断は未接続。',
 '全関数域・全領域の量化は保持する。有限検査では実際の質問と記録内容を評価し、量化の結合は二個体域への明示的な型置換で別に診断する。局所の試験例を無限域・物理法則・原文同義性の自動証明としない。',
]

def decoded(record):return [app(v(n),record) for n in ('electricreader','magneticreader')]
def encoded():return app(v('encoder'),*args(PAIR))
def candidate(question,values):return 'h['+question+']['+' '.join(values)+']'
def method_meta():
    replacements={'frame':v('newframe'),'lengthunit':k('ta'),'timeunit':k('rb'),'region':k('s6m',v('light'),v('speed'),v('region'))}
    return [replacements.get(n,v(n)) for n,t in META]
def method_task():return method_meta()+args(CODEC)+[k('ekv5',*args(SETTING))]
def transformed():return [k(n,v('light'),v('speed'),v('electricfield'),v('magneticfield')) for n in ('s6k','s6l')]

def definitions():
    text='r eisvj['+' '.join(t for n,t in PAYLOAD)+'] c.\n';rec=v('record')
    text+=define('ekv7',META+CODEC+[('record','a')],k('eisvj',rec,*args(META),*decoded(rec)))
    text+=define('ekwa',TASK+[('record','a')],both(k('ekv7',*args(META+CODEC),rec),candidate(v('question'),decoded(rec))))
    text+=define('ekwb',TASK,'j v[i[record a]['+k('ekwa',*args(TASK),rec)+']]','g[a]')
    pack=encoded()
    text+=define('ekwc',META+CODEC+PAIR,both(k('ekv7',*args(META+CODEC),pack),*(k('ejs3',got,want,v('region')) for got,want in zip(decoded(pack),args(PAIR)))))
    body=op('y',candidate(v('question'),args(PAIR)),both(k('ekwc',*args(META+CODEC+PAIR)),k('ekwa',*args(TASK),pack)))
    text+=define('ekwd',TASK,q('f','electric',FIELD,q('f','magnetic',FIELD,body)))
    text+=define('ekwe',ATTACH,q('f','record','a',op('z',candidate(app(v('questions'),v('problem')),[rec]),candidate(v('recordquestion'),[rec]))))
    text+=define('ekwf',METHOD,k('ekwb',*method_task()),'g[a]')
    text+=define('ekwg',METHOD,app(v('encoder'),*transformed()),'a')
    forward='i[point '+POINT+']['+k('s46',v('light'),v('speed'),v('point'))+']'
    inverse='i[point '+POINT+']['+k('s46',v('light'),k('be',v('speed')),v('point'))+']'
    charts=[k('eisqt',v(a),v(b),k('ta'),k('rb'),mapping,v('context')) for a,b,mapping in [('oldframe','newframe',forward),('newframe','oldframe',inverse)]]
    text+=define('ekwh',METHOD,both(*charts,k('ekv6',*args(SETTING)),k('ekwc',*method_meta(),*args(CODEC),*transformed()),candidate(k('ekwf',*args(METHOD)),[k('ekwg',*args(METHOD))])))
    text+=define('ekwi',METHOD,both(k('ekwd',*method_task()),k('ekwh',*args(METHOD))))
    text+=define('ekwj',LINK,both(k('ekwe',v('problem'),v('questions'),k('ekwf',*args(METHOD))),k('ekwi',*args(METHOD)),candidate(app(v('questions'),v('problem')),[k('ekwg',*args(METHOD))])))
    position=lambda xs,value:'a['+xs+']['+v('slot')+']['+value+']'
    text+=define('ekwk',SERIES,both(k('ekwj',*args(LINK)),position(v('targets'),v('problem')),position(v('answers'),k('ekwg',*args(METHOD))),k('ekvi',v('targets'),v('answers'),v('questions'))))
    return text

@lru_cache(None)
def build():
    old=parse(read(PARENT));assert len(old['statements'])==406
    assert not (set(MEANINGS)|set(PRIMITIVES))&{d['name'] for d in old['declarations']}
    doc=deepcopy(old);doc['statements']=[];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[n for n,t in PRIMITIVES[d['name']][0]],meaning_ja=PRIMITIVES[d['name']][1]) for d in added if d['kind']=='primitive'}
    basis=dict(status='typed_field_answer_records_connected_to_problem_series',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,new_signatures={d['name']:{key:d[key] for key in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(MEANINGS),statement_indices=[]).document
    ann=json.loads(read('data/body-rest-field-method-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode()))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}
