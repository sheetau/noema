"""Distinguish a role's competence requirement from its holder's actual skill."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT,closure

PARENT='examples/v016/kant-conditional-forecast.noema'
PARENT_BASIS='data/conditional-forecast-basis-v1.json'
FULL='examples/v016/kant-role-qualifications.noema'
CORE='examples/v016/role-qualifications-core.noema'
LIBRARY='examples/v016/role-qualification-relations.noema'
BASIS='data/role-qualifications-basis-v1.json'
ANNOTATIONS='data/role-qualifications-identifiers-v1.json'
PRIMITIVES={
 'hzwn':(['holder','role','scene'],'その状況で、その主体が社会的な実践の中で当該の役割を担う者として位置付けられている。役割の自己申告だけ、現在の行為、能力、資格要件の充足、法律上の免許の保有とは別の関係。実践の出所と範囲は状況の解釈で固定する。'),
 'hzwo':(['role','recipient_activity_description','scene'],'その実践の役割は、受け手について記述された活動の判断・指示・援助を供する機能を担う。役割の機能の内容であり、個々の受け手による活動の実行、供給者の現在の活動や成功は要求しない。'),
 'hzwp':(['role','holder_qualification_description','scene'],'その同じ実践で、この役割を担う者には、記述された性質を備えることが資格要件として求められている。要求の存在を表し、現に役割を持つ全員が要件を満たすこと、要件の正当性や法的な強制を意味しない。'),
 'hzwq':(['person','recipient_activity_description','scene'],'その人が、受け手について記述された活動に関する判断・援助を行うための、体系的な学習や経験を通じて獲得した専門的な知識・技能を備える。単なる関心、一度の成功、資格の名称や保持からは導かない。個々の判断の正しさ、無誤謬性、現代の特定の学位・免許を含意しない。知識と獲得の経験的な判定には根拠が必要である。'),
}
MEANINGS={
 'rqxh':'同じ役割と同じ状況について、主体がその役割を持ち、その役割が指定した受け手の活動を援助する機能を持ち、指定した主体の性質がその役割の資格要件として要求される。三つの関係の役割を共有する。資格の記述を実行して本人の実際の能力を判定する定義ではない。',
 'rqxi':'本人が、他者の身体的な健康の維持・回復についての判断sqを援助する専門的な知識・技能hzwqを備えるという内容。役割に課される資格の記述としても、本人の実際の性質としても、区別して用いる。',
 'rqxj':'人であり、他者についてsqの判断を援助する継続的な役割・実践siを担う。旧srの広い健康上の助言者の条件を保持する。この条件だけでは専門的な役割を識別しない。',
 'sr':'rqxjの健康上の継続的な助言者であり、同じ本人・状況にsqを援助する社会的な役割があり、その同じ役割には専門的な知識・技能rqxiが資格要件として求められている。医師についての構成的な部分説明を専門的な役割へ限定したもの。本人の無誤謬性や現代の免許は追加せず、他の健康専門職との歴史的な役割境界の確認は残る。',
}

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)

def build():
    old=parent();doc=deepcopy(old.document)
    assert not (set(PRIMITIVES)|{'rqxh','rqxi','rqxj'})&set(old.entries)
    at=next(i for i,d in enumerate(doc['declarations']) if d['name']=='sr')
    prefix=deepcopy(doc);prefix.update(declarations=doc['declarations'][:at],statements=[])
    raw=deepcopy(old.entries['sr']['declaration']);raw['name']='rqxj';prefix['declarations'].append(raw)
    text='''r hzwn[a a d] c.r hzwo[a i[h[a] e] d] c.r hzwp[a i[h[a] e] d] c.r hzwq[a i[h[a] e] d] c.
d rqxh[person a task i[h[a] e] qualification i[h[a] e] scene d holds h[a a d] c serves h[a i[h[a] e] d] c requires h[a i[h[a] e] d] c] c[
 g role a[w[c[v holds][v person v role v scene]][w[c[v serves][v role v task v scene]][c[v requires][v role v qualification v scene]]]]
].
d rqxi[person a] e[b scene[k hzwq[v person r[p sq] v scene]]].
d sr[person a scene d] c[w[k rqxj[v person v scene]][k rqxh[v person r[p sq] r[p rqxi] v scene p hzwn p hzwo p hzwp]]].'''
    parsed=parse(format_graph(prefix,'compact')+text)
    doc['declarations']=parsed['declarations']+doc['declarations'][at+1:]
    doc=parse(format_graph(doc,'compact'))
    basis=dict(status='role_requirements_separated_from_actual_competence',document=FULL,
        revises_document=PARENT,revises_meaning_basis=PARENT_BASIS,primitives={},definitions={},
        predecessor_source_sha256=old.source_sha256,
        limitations=['医師の部分説明を、専門的な知識・技能を求める社会的な役割へ限定する。看護など他の健康専門職との歴史的な区別は未確定。',
            '役割・その機能・資格要求・実際の知識獲得を四つの一般関係として明示する。社会制度や学習の全理論を定義したとはしない。',
            '書物、宗教上の助言者、良心、第二段落全体、二作品全文の意味確認は未完。'],
        unresolved=[dict(basis=r['basis'],historical_caveats=r['caveats']) for r in old.lineage])
    for d in doc['declarations']:
        n=d['name']
        if d['kind']=='primitive':
            labels,meaning=PRIMITIVES[n] if n in PRIMITIVES else (old.entries[n]['arguments'],old.entries[n]['meaning_ja'])
            basis['primitives'][n]=dict(parameters=d['parameters'],result=d['result'],arguments=labels,meaning_ja=meaning)
        else:basis['definitions'][n]=MEANINGS[n] if n in MEANINGS else old.entries[n]['meaning_ja']
    core=deepcopy(doc);core['statements']=[doc['statements'][4]]
    core['declarations']=closure(doc,_references(core['statements']))
    lib=deepcopy(doc);lib.update(declarations=closure(doc,['rqxh']),statements=[])
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/conditional-forecast-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

def main():
    from scripts.audit_opening_scope import write_exact
    for p,s in build().items():write_exact(ROOT/p,s)
    print('Role qualification composition written',flush=True)

if __name__=='__main__':main()
