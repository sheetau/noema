"""Ground a role-enactment reading in activity classification and execution."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT,v,call as k,app,both,op,definition
from scripts.compose_assumed_standing import PREMISE_FIELDS,ALL_FIELDS,CONTEXT
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/kant-assumed-standing.noema'
FIELDS=[('person','a'),('activity','a'),('standing','a'),('context','d')]
RELATIONS=[('positioned','h[a a a d] c'),('executes','h[a a d] c')]
PREMISE=[f for f in PREMISE_FIELDS if f[0]!='assumes']
ALL=[f for f in ALL_FIELDS if f[0]!='assumes']


def definitions():
    text=definition('rfs',params(FIELDS+RELATIONS),both(
        app(v('positioned'),*args(FIELDS)),app(v('executes'),v('person'),v('activity'),v('context'))))
    text+=definition('rft',params(FIELDS+RELATIONS+[('entrusted','h[a a d] c')]),both(
        k('rfs',*args(FIELDS+RELATIONS)),op('u',app(v('entrusted'),v('person'),v('standing'),v('context')))))
    return text


MEANINGS={
    'rfs':'同じ本人・活動・立場・状況について、活動がその立場での行為として位置付けられ、本人がその活動を実際に行う。計画上の役割分類だけや、別の行為の実行だけでは成立しない。',
    'rft':'rfsの実際の行為があり、同じ状況で同じ人へその職務・地位が委ねられていない。委任の不在という記述であり、禁止・不当性・条件不足・自発性を含まない。',
}
LIMITS=[
    '活動を立場へ位置付けることと実行の関係から、実際の役割遂行を構成する。本人による自由な選択、役割への自認、意図、制度的な権限は別の条件である。',
    'rftを不適切さの十分条件にしない。学識者としての公的発言など、委任を前提としない立場も記述できる。委任状態が未知なら、その不在を補わない。',
]


def generic_composed():
    doc=parse('n:'+definitions())
    basis=dict(version='enacted-standing-basis-v1',document='examples/v014/enacted-standing.noema',
        primitives=[],definitions=MEANINGS,unresolved=LIMITS)
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/kant-assumed-standing-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    text=definitions()
    text+=definition('hza7',params(FIELDS),k('rfs',*args(FIELDS),'p cb','p cg'))
    text+=definition('hzbd',params(FIELDS),k('rft',*args(FIELDS),'p cb','p cg','p cf'))
    for name,parent,fields,original in (
        ('hzba','hza4',PREMISE+CONTEXT,PREMISE_FIELDS+CONTEXT),
        ('hzbb','hza5',ALL+[('cases','h[d] c')],ALL_FIELDS+[('cases','h[d] c')]),
        ('hzbc','hza6',PREMISE+[('cases','h[d] c')],PREMISE_FIELDS+[('cases','h[d] c')])):
        text+=definition(name,params(fields),k(parent,*args(original,assumes='p hza7')))
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis.update(version='kant-enacted-standing-basis-v1',document='examples/v014/kant-enacted-standing.noema')
    basis['definitions'].update(MEANINGS|{
        'hza7':'既存cbによる活動・立場の対応とcgによる本人の実行を同じ引数で結び、その立場で実際に行為したことを構成する。caの理性使用分類やcfの職務委任は追加しない。',
        'hzbd':'hza7に対して同じ人・立場・状況の職務委任cfがないことを別に記述する。批判の評価条件へは自動追加しない。',
        'hzba':'先行hza4のassumesへ実際の役割遂行hza7を渡した読解候補。批判行為が同じ人のその立場での実行であり、明示した立場の条件に不足がある場合を扱う。自発的に役割を選んだことまでは表さない。',
        'hzbb':'hza5の条件文へ同じ実際の役割遂行を渡す。役割分類だけで未実行の批判を前件に数えない。職務委任の有無は、明示した条件列が参照する場合を除き評価に使わない。',
        'hzbc':'同じ実際の役割遂行の読みで前件に該当する事例が、指定仮定範囲に存在する。条件文の成立と前件の実例を分ける。',
    })
    basis['unresolved']+=LIMITS+[
        '先行版の「自ら立場を取る」という関係を、この候補では実際の役割遂行という明示した条件へ具体化した。本人の意図的な自己位置付けと完全に同義だとはしない。先行版の自由な関係引数も保持する。',
        '既存のcbによる活動と立場の対応、cgの実行、評価条件の採用根拠の一般的な基礎説明は残る。語義の唯一性やvorwitzigの意味一致をこの接続だけで確定しない。',
        'Skandal、sogar、demohngeachtet、制度の説明、全文の意味確認は未完。新しい基本記号・著者主張・対応原文範囲は追加しない。',
    ]
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def core_composed():
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=['hzba','hzbb','hzbc','hzbd','hzah','rfd'],statement_indices=[])
    projected=extract_basis(doc,basis,selected,version='enacted-standing-core-basis-v1',document_path='examples/v014/enacted-standing-core.noema')
    return format_graph(selected.document,'compact')+'\n',projected


BUILDERS=((generic_composed,'enacted-standing'),(source_composed,'kant-enacted-standing'),(core_composed,'enacted-standing-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored enacted standing differs: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
