"""Separate discretionary grants, fulfilled duties and unwarranted claimed latitude."""
from copy import deepcopy
import json
from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params,args
from scripts.compose_scoped_nonprescription import DUTY,SOURCE_DUTY
from scripts.compose_described_norms import TRUE

PARENT='examples/v014/kant-label-refusals.noema'
CLAIM=[('person','a'),('activity','a'),('standing','a'),('assumes','h[a a a d] c')]+DUTY
SOURCE_CLAIM=CLAIM[:-2]
ROOTS=['rnk','rnl','rnm','rnn','rno']


def definitions():
    valid='i[items j[a]]['+k('rdr',v('items'),'n p b b')+']'
    permitted=lambda sign:k('rdu',v('assessor'),v('person'),v('office'),v('policy'),v('bindings'),sign,v('context'),valid,v('required'),v('allowed'))
    choice=both(k('rdr',v('bindings'),'n p b b'),quant('g','person','a',both('a[v bindings][n p a b][v person]',permitted(TRUE),permitted(op('u',TRUE)))))
    text=definition('rnk',params(DUTY),'i[bindings j[a]][b context['+choice+']]', 'h[j[a]] e')
    actual=op('t',app('s[v policy]',v('bindings')),v('context'))
    for name,target in (('rnl','rnk'),('rnm','rm7')):
        content=op('t',app(k(target,*args(DUTY)),v('bindings')),v('context'))
        text+=definition(name,params(DUTY),'i[bindings j[a]][b context['+both(content,actual)+']]', 'h[j[a]] e')
    criterion=both(op('e',v('standing'),v('selected')),op('t',app(k('rnk',*args(DUTY)),'l[a][v person]'),v('context')))
    text+=definition('rnn',params([('selected','a')]+DUTY),'i[person a standing a][b context['+criterion+']]', 'h[a a] e')
    text+=definition('rno',params(CLAIM),k('rfq',v('activity'),v('person'),v('standing'),
        'l[h[a a] e]['+k('rnn',v('standing'),*args(DUTY))+']',v('assumes')), 'e')
    return text

MEANINGS={
    'rnk':'ちょうど一人の引数について、同じ評価出所・本人・立場・政策記述・文脈で、政策の成立と不成立の双方が積極的に許され、それぞれの反対要求がないという内容。実行能力や制度変更権限とは別の規範上の裁量。',
    'rnl':'rnkの裁量があり、その同じ政策が同じ本人の引数で現に成立する。対象記述を脱引用して評価するため、引用前には既知の閉じた記述への特殊化が必要。',
    'rnm':'rm7の政策成立への義務があり、同じ政策が同じ本人の引数で現に成立する。履行の条件であり、義務の正当性や規範体系の無矛盾性までは主張しない。引用にはrnlと同じ制約がある。',
    'rnn':'指定した裁量上の立場について、同じ本人がrnkを満たすという資格条件。立場の同一性と対象政策を固定し、別の立場への資格へ流用しない。',
    'rno':'同じ本人が同じ行為・文脈で裁量上の立場を自ら取り、その立場のrnnの条件が不成立である。現実の政策の不実行や許可の欠如だけを、立場を取る行為へ変換しない。',
    'hzfx':'rnkを既存の政策規範h7k・h7lへ接続する。内側の自由政策の規範源と外側の裁量評価の出所は別に保持する。',
    'hzfy':'rnlをh7k・h7lへ接続する。自由を認める政策を選べることと、実際に自由を認めることの両方を要求する。',
    'hzfz':'rnmをh7k・h7lへ接続し、同じ自由政策が義務であることとその成立を区別した上で結ぶ。',
    'hzf2':'rnoの資格条件をh7k・h7lへ接続する。裁量のない本人が裁量上の立場を自ら取るという評価候補で、名称使用の事実を補わない。',
}
LIMITS=[
    '自由を残すことが義務であるという前段と、寛容という傲慢な名称を拒むという原文の接続に対し、自由を授けるか控えるかを選べる側という自己位置付けを対照させる解釈候補。原文はこの規範モデルを明記していない。',
    '裁量は肯否の積極的な許可と反対要求の不在で構成する。要求が見つからないことだけでは裁量としない。裁量があることから、政策を実現する能力、他者の権利を変更する権能、統治の正当性を補わない。',
    '寛容一般には不賛同、抑制、非干渉など別の捉え方もあり、この裁量的許可を寛容の唯一の必要十分条件にしない。原文の名称が持つ社会的含意との対応は未完である。',
    'rnoは立場を取る行為と明示的な資格条件の不充足を結ぶ。侮蔑・優越感・虚栄・性格としての傲慢の一般理論ではない。名称の適用からその立場を取ることを導く慣習上の説明も残る。',
    '同じ政策の実行が要求されるならrnkは不成立になる。相反する要求が共存する場合にも裁量とはせず、rnmによる履行の有無と無矛盾性を別に扱う。',
    '規範の内容と出所、本人・立場・政策記述・引数列・文脈を固定する。基準の正当性は入力に依存し、未知の規範を偽や許可で補わない。',
    '宗教と良心の概念、権利、寛容の文化的意味、名称への評価の著者帰属と論証、品位、称賛、政府による解放、段落全体の意味確認は残る。原始記号と著者主張は追加しない。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    text=definitions()
    for name,target in (('hzfx','rnk'),('hzfy','rnl'),('hzfz','rnm')):
        text+=definition(name,params(SOURCE_DUTY),k(target,*args(DUTY,required='p h7k',allowed='p h7l')), 'h[j[a]] e')
    text+=definition('hzf2',params(SOURCE_CLAIM),k('rno',*args(CLAIM,required='p h7k',allowed='p h7l')), 'e')
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/kant-label-refusals-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-policy-discretion-basis-v1',document='examples/v014/kant-policy-discretion.noema')
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS;audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text);selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed():return projected(ROOTS+['rm2','rm3','rm4','rm5','rm6','rm7','rlg'],'policy-discretion')
def core_composed():return projected(ROOTS+['rm2','rm3','rm4','rm5','rm6','rm7','rlg','hzfn','hzfo','hzfp','hzfq','hzfx','hzfy','hzfz','hzf2','fa','fb'],'policy-discretion-core')
BUILDERS=((generic_composed,'policy-discretion'),(source_composed,'kant-policy-discretion'),(core_composed,'policy-discretion-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored policy discretion differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
