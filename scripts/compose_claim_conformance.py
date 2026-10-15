"""Separate person-indexed requirements, fulfillment and their stability."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from scripts.compose_self_benefit import ROOT,SOURCE as PARENT
from scripts.compose_governing_principles import DESCRIPTION,RULE,TRUE
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_collective_office import params,av
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive

LIBRARY='examples/v016/claim-conformance.noema'
SOURCE='examples/v016/kant-claim-conformance.noema'
CORE='examples/v016/claim-conformance-core.noema'
BASIS='data/claim-conformance-basis-v1.json'
REVIEW='data/dignity-reading-v1.json'
IDENTITY=[('source','a'),('actor','a'),('office','a'),('person','a')]
TARGETS=[('claims','j[a]'),('scope','h[a] c'),('description','h[a] '+DESCRIPTION)]
FIELDS=IDENTITY+TARGETS+[('context','d'),('required',RULE)]
STABLE=IDENTITY+TARGETS+[('cases','h[d] c'),('required',RULE)]
COMBINED=FIELDS[:-1]+[('cases','h[d] c'),('required',RULE)]
ROOTS=['ryb','ryc','ryd','rye','ryf']


def definitions():
    inventory=k('rcm',v('claims'),v('scope'))
    target=app(v('description'),v('claim'));bindings='l[a][v actor v person]'
    norm=app(v('required'),v('source'),v('actor'),v('office'),target,bindings,TRUE,v('context'))
    fulfilled=op('t',app('s['+target+']',bindings),v('context'))
    each=lambda body:quant('f','claim','a',op('y',app(v('scope'),v('claim')),body))
    text=definition('ryb',params(FIELDS),both(inventory,each(norm)))
    text+=definition('ryc',params(IDENTITY+TARGETS+[('context','d')]),both(inventory,each(fulfilled)))
    text+=definition('ryd',params(FIELDS),both(k('ryb',*av(FIELDS)),k('ryc',*av(FIELDS[:-1]))))
    refs={n:v(n) for n,t in FIELDS};refs['context']=v('candidate')
    text+=definition('rye',params(STABLE),both(inventory,quant('g','candidate','d',app(v('cases'),v('candidate'))),
        quant('f','candidate','d',op('y',app(v('cases'),v('candidate')),k('ryb',*[refs[n] for n,t in FIELDS])))))
    text+=definition('ryf',params(COMBINED),both(k('rye',*av(STABLE)),k('ryd',*av(FIELDS))))
    return text


def additions():
    text=''.join(primitive('iau'+name,sort) for name,sort in (
        ('claims','h[a d] j[a]'),('scope','h[a d a] c'),('description','h[a] '+DESCRIPTION)))
    fields=IDENTITY+[('anchor','d'),('context','d'),('cases','h[d] c')]
    refs={n:v(n) for n,t in fields}
    refs.update(claims=k('iauclaims',v('person'),v('anchor')),
        scope='i[claim a][k iauscope[v person v anchor v claim]]',description='p iaudescription',required='p h7k')
    text+=definition('iaustanding',params([f for f in fields if f[0]!='context']),both(k('aa',v('person')),
        k('rye',*[refs[n] for n,t in STABLE])))
    text+=definition('iautreatment',params(fields),both(k('aa',v('person')),k('ryf',*[refs[n] for n,t in COMBINED])))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib=deepcopy(parent);lib['statements']=[];lib['declarations']=closure(parent,['rcm'])
    lib=parse(format_graph(lib,'compact')+definitions())
    doc=deepcopy(parent);statements,doc['statements']=doc['statements'],[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions());doc['statements']=statements
    core=deepcopy(doc);core['statements']=[];core['declarations']=closure(doc,ROOTS+['iaustanding','iautreatment'])
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='person_indexed_claim_conformance_and_scoped_normative_stability',parent=PARENT,document=SOURCE,
        definitions={
            'ryb':'非空で完全列挙した同じ基準について、同じ出所が同じ行為主体にその職務で、その本人に対する内容の実現を要求する。対象記述に行為主体・本人の順序付き二個体列を渡す。',
            'ryc':'rybと同じ基準記述と二個体列について、同じ文脈で各内容が実際に成立する。要求の存在は別に扱う。',
            'ryd':'要求rybと実際の履行rycがともに成立する。利益や意図だけで履行を代用しない。',
            'rye':'指定した非空の比較状況全てで、同じ本人に関する同じ基準への要求rybが維持される。基準の履行が失われても要求自体は残り得る。',
            'ryf':'比較状況を通じた要求の維持ryeと、現在の要求・履行rydの両方が成立する。比較範囲に現在が含まれなくても現在の要求は別に検査する。',
            'iaustanding/iautreatment':'基準の本人を人aaに限定し、元の本人・基準時点で固定した基準一覧を既存のh7kへ結ぶ。比較状況ごとに本人や守るべき基準を交換しない。'},
        limitations=[
            '基準の内容はNoemaの記述として与える。名称だけで尊厳や敬意を定義したものではない。具体的な基準、その道徳的根拠、人格・自律・目的それ自体の説明は残る。',
            '要求の存在と内容の実現を分離する。好意・有益さ・利益の増加・善意があっても、同じ基準内容が不成立ならryd/ryfは不成立である。逆に利益がないことだけで要求や履行を否定しない。',
            'ryeは指定状況間の規範の不変性であり、あらゆる利益や交換に対する不可侵性・無条件の尊厳の証明ではない。比較状況の選定と網羅性は別に説明しなければならない。',
            '個人に対して守られる内容を二個体の順序付き列で保持する。h7kの規範源・職務と、対象となる本人は別である。第三者への履行や逆順の内容で本人への扱いを補わない。',
            '現在の履行は現実の真偽として評価するが、原則自体の内容は条件付きでもよい。具体的な行為があったか、複数の要求が整合的か、制度的に有効かを一般形だけで保証しない。',
            '動的に与えた基準記述を脱引用するため、iautreatmentの引用には少なくとも階数1が必要である。既存の階数0の政策引数へそのまま渡せず、具体的基準への静的特殊化か型の明示的な拡張が必要になる。',
            '親の全宣言と全22主張を保存する。具体的な尊厳の内容と政府の原則への接続は未完で、新しい著者主張・原文範囲・意味確認済み区間は追加しない。'])


def reading_review():
    from scripts.check_apparent_liberty import UNITS
    unit=next(u for u in json.loads((ROOT/UNITS).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0017')
    return dict(source_unit=unit['id'],source_sha256=unit['text_sha256'],checked_on='2026-10-15',
        sources=[
            dict(url='https://www.korpora.org/Kant/aa08/042.html',lines='1-2',scope='対象論説',observation='人間と機械の対比に続き、その人間の尊厳に即した扱いを述べる。ここだけに尊厳の定義や具体的な行為基準は列挙されない。'),
            dict(url='https://www.korpora.org/kant/aa04/434.html',lines='20-34',scope='別著作の比較資料',observation='尊厳に基づく義務を将来の利益から区別し、価格と等価物による代替を許さない価値を対比する。'),
            dict(url='https://www.korpora.org/kant/aa04/435.html',lines='2-17,25-28',scope='別著作の比較資料',observation='内的価値と相対的な価格、道徳性と人間性、利益の結果に還元されない価値を論じる。')],
        decisions=['別著作の説明を1784年の当該語義と自動同一化しない。今回の一般用構成は、規範上の基準とその履行を区別する準備である。',
            '直前に作った政府の自己利益判断を、尊厳や尊厳に即した扱いの真偽へ流用しない。利益を得る主体と扱いの対象になる人を分ける。',
            '有限の比較状況で要求が変わらないことを、全ての価格・等価物に対する非代替性や人間の尊厳全体と同義にしない。'])


def main():
    files=build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n',REVIEW:json.dumps(reading_review(),ensure_ascii=False,indent=2)+'\n'}
    for name,body in files.items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
