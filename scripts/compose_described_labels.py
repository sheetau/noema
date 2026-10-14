"""Connect designation use to an explicit reusable description and adopted stance."""
from copy import deepcopy
import json
from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both
from scripts.compose_situated_criticism import params,args
from scripts.compose_label_refusals import USE
from scripts.compose_scoped_nonprescription import SOURCE_DUTY

PARENT='examples/v014/kant-policy-discretion.noema'
PATTERN='i[h[a] e]'
EXPLANATION=[('pattern',PATTERN),('argument','i[a]'),('instance','i[e]'),('stored','h[a '+PATTERN+' d] c')]
USE_FIELDS=USE+EXPLANATION
ADOPTION=[('use','h[a a a d] c'),('applied','h[a i[e] a d] c')]
ALL=USE_FIELDS+ADOPTION
FIXED=[(n,t) for n,t in ALL if n not in ('speaker','activity','subject','context')]
SOURCE_FIXED=[(n,t) for n,t in FIXED if n not in ('occurs','presents','stored','use','applied')]
ROOTS=['rnp','rnq','rnr','rns','rnt']


def definitions():
    text=definition('rnp','policy h[j[a]] e','i[person a]['+app(v('policy'),'l[a][v person]')+']','h[a] e')
    match=k('rbp',v('label'),v('pattern'),v('argument'),v('instance'),v('context'),v('stored'))
    text+=definition('rnq',params(USE_FIELDS),both(k('rnh',*args(USE)),match,op('e','s[v argument]',v('subject'))))
    adoption=k('rbq',v('speaker'),v('label'),v('activity'),v('pattern'),v('argument'),v('instance'),v('context'),v('stored'),v('use'),v('applied'))
    text+=definition('rnr',params(ALL),both(k('rnq',*args(USE_FIELDS)),adoption))
    text+=definition('rns',params(ALL),both(op('e',v('speaker'),v('subject')),k('rnr',*args(ALL))))
    condition=both(op('e',v('standing'),v('selected')),k('rns',*args(ALL,subject=v('speaker'))))
    text+=definition('rnt',params([('selected','a')]+FIXED),'i[speaker a activity a standing a context d]['+condition+']','h[a a a d] c')
    return text

MEANINGS={
    'rnp':'一人の引数列を取る政策内容を、同じ一人から内容への性質にする。意味を文字列へ置き換えず、閉じた性質記述の構成に使える。',
    'rnq':'同じ名称の実際の適用行為を、その名称が保持する性質記述、引数記述、構文上正確な適用例へ接続する。引数記述を評価した対象と、名前を付けられた実際の対象が同一である。性質の真理は要求しない。',
    'rnr':'rnqの同じ人・名称・行為について、本人が表現を使い、その同じ適用例を同じ行為の言い方や定め方として採っている。引用や他人の語の報告だけでは採用を補わない。',
    'rns':'rnrで名前を適用する対象が話者本人である。別人をそう呼ぶことから本人の自己位置付けを作らない。',
    'rnt':'名称・意味記述・適用例・使用関係を固定し、rnsの自己適用を指定した立場を取る関係の構成候補にする。どの立場を表す意味記述かは接続例でそろえ、型だけで任意の意味と立場を同一視しない。',
    'hzf3':'自由を残す政策を裁量によって実現するhzfyの内容を、rnpで人物の性質へ変換する。寛容という名称への批判を読むための説明候補であり、寛容一般の必要十分条件ではない。',
    'hzf4':'rntを既存の名称適用行為dg・f3、意味型の保持hw2、使用hx2、適用例の採用hy2へ接続する。assumes引数へ渡して、前段の裁量の資格条件と結合できる。',
}
LIMITS=[
    '名称の参照から、Noemaで構成した人物の性質記述までを明示的につなぐ。原語の綴り、対訳表、埋め込んだ自然言語の説明を意味本体として使わない。',
    '保持された意味記述と構文上の適用例は既存rbp・rbq・rboで検査する。別名の展開や同じ真理値による置換はしない。対象の同定には引数記述だけを脱引用し、性質の真理をそこから補わない。',
    'hw2の保持はその文脈の説明規約として与える。社会全体の合意、歴史的な語義、話者の全ての信念を証明する関係ではない。別の文脈や名称へ意味を自動で移さない。',
    'rntは指定した記述の自己適用を立場の表明として読む構成である。裁量を表す性質と裁量上の立場を結ぶ接続例以外へ、無条件にその意味を一般化しない。',
    'hzf3は政策の実現を含むため、引用前に既知の閉じた政策記述へ特殊化する。未知の規範や許可があっても名前の使用や採用を記述でき、真理評価を求めた場合だけ必要な入力を要求する。',
    '原文の寛容という名称と傲慢という評価の一つの説明候補。現実の語用慣習、婉曲・反語、寛容一般に含まれる不賛同や抑制、評価の著者帰属と論証、称賛と全文の意味確認は残る。原始記号と著者主張は追加しない。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    text=definitions()+definition('hzf3',params(SOURCE_DUTY),k('rnp',k('hzfy',*args(SOURCE_DUTY))),'h[a] e')
    text+=definition('hzf4',params([('selected','a')]+SOURCE_FIXED),k('rnt',v('selected'),*args(FIXED,occurs='p dg',presents='p f3',stored='p hw2',use='p hx2',applied='p hy2')),'h[a a a d] c')
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/kant-policy-discretion-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-described-labels-basis-v1',document='examples/v014/kant-described-labels.noema')
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS;audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text);selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed():return projected(ROOTS+['rnk','rnl','rnm','rnn','rno','rm2','rm3','rm4','rm5','rm6','rm7','rlg'],'described-labels')
def core_composed():return projected(ROOTS+['rnk','rnl','rnm','rnn','rno','rm2','rm3','rm4','rm5','rm6','rm7','rlg','hzfn','hzfo','hzfp','hzfq','hzfx','hzfy','hzfz','hzf2','hzf3','hzf4','fa','fb'],'described-labels-core')
BUILDERS=((generic_composed,'described-labels'),(source_composed,'kant-described-labels'),(core_composed,'described-labels-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored described labels differ: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
