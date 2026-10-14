"""Describe retaining an adopted standard without asserting its performance."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant
from scripts.compose_situated_criticism import params,args
from scripts.compose_adopted_standards import DESCRIPTION,DESCRIBED_ADOPTION

PARENT='examples/v014/kant-mutual-undertakings.noema'
VERSION='h[a a d] '+DESCRIPTION
POINT=[('organization','a'),('standard','a'),('description',DESCRIPTION),('scene','d'),
    ('versions',VERSION),('adopted',DESCRIBED_ADOPTION)]
INTERVAL=[(n,t) for n,t in POINT if n!='scene']+[
    ('anchor','d'),('history','h[d] c'),('scope','h[d] c'),('before','h[d d] c')]
POLICY=INTERVAL[:5]+[('histories','h[d] h[d] c'),('scopes','h[d] h[d] c'),('orders','h[d] h[d d] c')]
SOURCE=[(n,t) for n,t in POLICY if n!='orders']
ROOTS=['rh3','rh4','rh5']


def definitions():
    text=definition('rh3',params(POINT),both(
        op('e',app(v('versions'),v('organization'),v('standard'),v('scene')),v('description')),
        app(v('adopted'),v('organization'),v('standard'),v('description'),v('scene'))))
    future=op('x',op('e',v('scene'),v('anchor')),app(v('before'),v('anchor'),v('scene')))
    body=both(k('tb',v('history'),v('scope'),v('before')),app(v('scope'),v('anchor')),
        quant('f','scene','d',op('y',app(v('scope'),v('scene')),both(future,k('rh3',*args(POINT))))))
    text+=definition('rh4',params(INTERVAL),body)
    # The shared institutional outcome is the same for each undertaking party.
    # Personal belief, individual performance and truth are separate predicates.
    body=k('rh4',*args(INTERVAL,anchor=v('context'),history=app(v('histories'),v('context')),
        scope=app(v('scopes'),v('context')),before=app(v('orders'),v('context'))))
    text+=definition('rh5',params(POLICY),'i[bindings j[a]][b context['+body+']]','h[j[a]] e')
    return text


MEANINGS={
    'rh3':'同じ組織・基準・状況に割り当てた版が指定した閉じた基準列記述と同一であり、その組織がその記述を採用している。採用と版の同一性を別に要求し、基準内容の真理や個人の信念は評価しない。',
    'rh4':'基準時を含む、同じ順序履歴内の非空で間の抜けない将来区間の全状況でrh3が成立する。最初と最後だけの一致や、途中の離脱を見逃す範囲は認めない。有限区間も許し、永久性や変更不能性そのものは主張しない。',
    'rh5':'rh4による基準保持を、個体引数列から状況ごとの内容への条項関数にする。履歴・区間・順序は評価文脈で固定し、その区間内で選び直さない。引数列に依存しない共同の制度的な結果を対象とし、各人の行為義務や信念と同一視しない。',
}
LIMITS=[
    'versionsは同じ組織と基準に現時点で指定されている版を閉じたNoemaの基準列記述で返す全域関数。現実の版管理・識別・欠落を認定する仕組みは別に必要。採用がない場合はadoptedで区別する。',
    '同じ関数値になる別名、並べ替え、追加、削除も記述の変更として検出する。この構文上の同一性は、教理の意味上の同義性や表記変更の許容規約と同一ではない。',
    '採用関係は既存の基準採用と同じ型・意味規約を用いる。宗教・教会・教理の一般的な構成説明、特定の信条の内容や採用の正当性はまだ確定していない。',
    'rh4は明示した区間で実際に保持される条件、rh5はその内容の構成。閉じたrh5の適用記述を引受け対象へ渡しても、実際の保持、未来の成功、内容の真理、個人の確信は導かない。',
    '区間の全状況は、その履歴と粒度の解釈で定まる。有限観測の成功を全時間の不変性と扱わない。終点のない時間、変更権能の不在、反事実的に変更できないことは別の条件である。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements,doc['statements']=doc['statements'],[]
    orders='i[anchor d][i[first d second d]['+k('ic',v('first'),v('second'),v('anchor'))+']]'
    extra=definitions()+definition('hzcj',params(SOURCE),k('rh5',*args(POLICY,orders=orders)),'h[j[a]] e')
    doc=parse(format_graph(doc,'compact')+extra);doc['statements']=statements
    basis=deepcopy(json.loads((ROOT/'data/kant-mutual-undertakings-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-fixed-standards-basis-v1',document='examples/v014/kant-fixed-standards.noema')
    basis['definitions'].update(MEANINGS|{'hzcj':'rh5の履歴の順序を同じ評価文脈のicへ結ぶ。既知の閉じた引数を適用した記述を、そのままhzcg等の相互引受けの条項とする。宣誓、制度上の拘束力、個別の教理内容は追加しない。'})
    basis['unresolved']+=LIMITS+[
        'u0013の一定で変更しない信条への部分的な解釈注記。指定した基準を変えず採用し続ける共同の内容を引き受ける候補であり、unveränderlichの全語義や永久性を有限区間へ確定したものではない。',
        '前版の相互引受けへ型付きの閉じた条項を接続できることを検査する。著者への帰属、問い、誓い、共同体の制度、永続的な後見の目的と全体の無効性判断の接続は未完。']
    audit_basis(doc,basis);return format_graph(doc,'compact')+'\n',basis


def projected(roots,stem):
    text,basis=source_composed();doc=parse(text);selected=extract_document(doc,roots=roots,statement_indices=[])
    result=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path='examples/v014/'+stem+'.noema')
    return format_graph(selected.document,'compact')+'\n',result


def generic_composed():return projected(ROOTS,'fixed-standards')
def core_composed():return projected(ROOTS+['hzcj','hzcg','hzch','hzci'],'fixed-standards-core')
BUILDERS=((generic_composed,'fixed-standards'),(source_composed,'kant-fixed-standards'),(core_composed,'fixed-standards-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored fixed standard differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
