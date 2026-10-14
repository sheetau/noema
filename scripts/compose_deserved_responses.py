"""Describe deserved responses separately from their performance and obligation."""
from copy import deepcopy
import json
from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both
from scripts.compose_situated_criticism import params,args,MESSAGE
from scripts.compose_qualified_princes import QUALIFIERS

PARENT='examples/v014/kant-qualified-princes.noema'
RESPONSE='i[h[a a a] e]'
BASIS='i[h[a] e]'
STANDARD='h[a '+RESPONSE+' '+BASIS+'] e'
SETTINGS=[('response',RESPONSE),('basis',BASIS),('standards','j['+STANDARD+']')]
PRESENTATION=[('audience','h[a] c'),('message',MESSAGE),('occurs','h[a d] c'),('presents','h[a a d] c'),('conveys','h[a a a '+MESSAGE+' d] c')]
ROOTS=['ro5','ro6','ro7','roa']


def definitions():
    criterion=op('t',app(v('standard'),v('subject'),v('response'),v('basis')),v('context'))
    allfit='q[v standards][e[n p a b][n p a b]][i[previous c standard '+STANDARD+']['+both(v('previous'),criterion)+']]'
    ground=op('t',app('s[v basis]',v('subject')),v('context'))
    text=definition('ro5',params([('subject','a')]+SETTINGS),'b context['+both(ground,op('u',op('e','d[v standards]','n p a b')),allfit)+']','e')
    text+=definition('ro6',params(SETTINGS),'i[subject a]['+k('ro5',v('subject'),*args(SETTINGS))+']','h[a] e')
    text+=definition('ro7','quality h[a] e','i[subject a][j s['+app(v('quality'),v('subject'))+']]','h[a] f')
    body=k('rfo',v('speaker'),v('activity'),v('audience'),v('subject'),v('message'),v('context'),v('occurs'),v('presents'),v('conveys'))
    text+=definition('roa',params(PRESENTATION),'i[speaker a activity a subject a][b context['+body+']]','h[a a a] e')
    return text

MEANINGS={
    'ro5':'対象者について指定根拠内容が成立し、非空の明示基準列の全てが、同じ対象者・応答行為記述・根拠記述について成立するという内容。応答に値することの根拠と基準を明示した構成候補。応答の実行や義務を要求しない。',
    'ro6':'応答記述・根拠記述・基準列を固定し、ro5を対象者ごとの内容関数にする。対象者を応答行為の話者にすり替えない。',
    'ro7':'対象者について指定性質内容を主張する発話関数。称賛の接続例では肯定的な評価内容を渡す。任意の肯定文だけで称賛の全意味とはしない。',
    'roa':'同じ話者・提示行為・対象者について、非空の受け手範囲へ同じ発話記述を提示する行為内容関数。応答記述では第三引数を評価対象者に固定する。',
    'hzgb':'roaの生起・提示者・伝達をdg・f3・f2へ接続する。対象者についての称賛候補を述べる行為と、その対象者が称賛に値するという評価を分ける。',
    'hzgc':'rnzで限定した同じ人物について、h4lの能力内容とro6の根拠付き応答適合をともに結論とする一般命題。存在・実際の称賛・称賛の義務を断言しない。',
}
LIMITS=[
    '応答に値することを、真の根拠内容と非空の明示的な応答適合基準で説明する候補。基準を満たすだけで道徳的に正当だと保証しない。基準の内容・採用根拠・責任や功績との関係の説明は別途必要である。',
    '称賛の作例では自由政策の実現を肯定的に取り上げる。肯定的評価の強さ、敬意や感情、皮肉、媒体、受け手の理解は未完。肯定的な事実報告と称賛を型だけで区別できるとはしない。',
    '発話の記述、応答の記述、対象者についての根拠の記述を保持する。同じ真理値の別記述へ適合基準を自動で移さない。基準関数が内部で何を評価するかは指定された基準による。',
    '応答に値することから特定話者の義務や許可、実際の発話、将来必ず称賛されることを導かない。対象者が反対に称賛者になる読みも補わない。',
    '応答記述は話者・行為・対象者の三引数を持つ。ro5は応答そのものを実行せず記述を基準へ渡す。根拠は対象者の一引数で評価し、応答行為を根拠の個体として使わない。',
    '原文のverdientとgepriesen zu werdenへの部分注記。世界と後世の集団・時点、感謝、最初の解放者という功績、政府による解放の全内容、全文の意味一致は未完。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    text=definitions()+definition('hzgb',params(PRESENTATION[:2]),k('roa',*args(PRESENTATION,audience=v('audience'),message=v('message'),occurs='p dg',presents='p f3',conveys='p f2')),'h[a a a] e')
    consequence='i[subject a][b context['+both(op('t',k('h4l',v('subject')),v('context')),op('t',k('ro5',v('subject'),*args(SETTINGS)),v('context')))+']]'
    text+=definition('hzgc',params(QUALIFIERS+SETTINGS),k('ro2',k('rnz',*args(QUALIFIERS)),consequence),'e')
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/kant-qualified-princes-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-deserved-responses-basis-v1',document='examples/v014/kant-deserved-responses.noema')
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS;audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text);selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed():return projected(ROOTS,'deserved-responses')
def core_composed():
    roots=[d['name'] for d in parse((ROOT/'examples/v014/qualified-princes-core.noema').read_text(encoding='utf-8'))['declarations']]
    return projected(roots+ROOTS+['hzgb','hzgc'],'deserved-responses-core')
BUILDERS=((generic_composed,'deserved-responses'),(source_composed,'kant-deserved-responses'),(core_composed,'deserved-responses-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored deserved response differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
