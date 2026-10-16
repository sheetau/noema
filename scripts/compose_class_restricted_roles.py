"""Restrict adopted roles by their content rather than by object identity."""
from copy import deepcopy
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure

PARENT='examples/v016/kant-exploratory-question.noema'
PARENT_BASIS='data/exploratory-question-basis-v1.json'
FULL='examples/v016/kant-class-restricted-roles.noema'
LIBRARY='examples/v016/class-restricted-roles.noema'
BASIS='data/class-restricted-roles-basis-v1.json'
ANNOTATIONS='data/class-restricted-roles-identifiers-v1.json'
MEANINGS={
 'rqrw':'指定された位置付けが同じ提示者・文献・文脈で採用され、その同じ範囲で採用される全位置付けが与えた性質を満たす。異なる位置付け個体を複数採っても、全てが性質を満たせばよい。空の採用、別の提示者・文献・文脈の採用を代わりにしない。',
 'hzle':'著者waが現在の論説hzikを今ここに置くことを容認し、この箇所で採る全ての提示上の位置付けを、同じ問いhzldを検討する試みという種類に限定する。hzlaの採用を要求するが、同じ問いに向く別の位置付け個体も許す。問いの記述を接続し、答えや現実の一致を肯定しない。',
}


def build():
    cat=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(cat.document)
    assert 'rqrw' not in cat.entries
    generic=parse('p:d rqrw[person a document a role a context d assigns h[a a a d] c qualifies h[a] c] c['
        'w[c[v assigns][v person v document v role v context]]'
        '[f other a[y[c[v assigns][v person v document v other v context]][c[v qualifies][v other]]]]].')['declarations'][0]
    at=next(i for i,d in enumerate(doc['declarations']) if d['name']=='hzle')
    doc['declarations'].insert(at,generic)
    prefix=deepcopy(doc);prefix['statements']=[];prefix['declarations']=doc['declarations'][:at+1]
    revised=parse(format_graph(prefix,'compact')+
        'd hzle[] c[w[k hzlb[k wa[] k hzik[] k hzjm[] k hzjl[]]]'
        '[k rqrw[k wa[] k hzik[] k hzla[] k hzjl[] p hzkz '
        'i[role a][k hzky[v role r[k hzld[]] k hzjl[]]]]]].')['declarations'][-1]
    doc['declarations'][at+1]=revised;doc=parse(format_graph(doc,'compact'))
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqrv','rqrw'])
    primitives=[];definitions={}
    for d in doc['declarations']:
        n=d['name'];entry=cat.entries.get(n)
        if d['kind']=='primitive':
            primitives.append(dict(symbol=n,parameters=d['parameters'],result=d['result'],arguments=entry['arguments'],meaning_ja=entry['meaning_ja']))
        else:definitions[n]=MEANINGS[n] if n in MEANINGS else entry['meaning_ja']
    basis=dict(status='class_restriction_instead_of_singleton_role_identity',document=FULL,library=LIBRARY,
        revises_document=PARENT,revises_meaning_basis=PARENT_BASIS,
        revision=dict(changed_bodies=['hzle'],new_definitions=['rqrw'],new_primitives=0),
        primitives=primitives,definitions=definitions,
        limitations=[
            'nurを同じ問いを検討する試みという種類への限定と読む。異なる位置付けの個体数が一つであるとはしない。',
            'hzlaの採用を一つの証人として残す。他の採用も同じ問いを検討する試みでなければならない。単に何らかの試みであるだけでは通らない。',
            '制約は同じ提示者・文献・文脈での位置付けに限る。文献の全目的・価値や、他者・別文脈での位置付けを制限しない。',
            '問いの内容は引き続き記述として接続する。思想の一致、偶発性、問いの答え、試みの成功は主張しない。',
            '性質の判定や採用関係が未知なら補わない。標準の非短絡評価器は採られていない位置付けの未知判定にも保留し得る。短絡診断と区別する。',
            '前版の他の意味規約・本文23文の構文を保存する。脚注全体の未解決事項は継承し、原文対応範囲と意味確認済み単位を増やさない。',
        ],
        superseded_parent_limitations=['hzleでrqrvを使い、位置付け個体をhzla一つに限定していた読みを撤回する。rqrv自体は厳密な単一個体限定を表す一般定義として保存する。'],
        unresolved=[dict(basis=row['basis'],historical_caveats=row['caveats']) for row in cat.lineage],
        predecessor_source_sha256=cat.source_sha256)
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/exploratory-question-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest())
    return {FULL:body,LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',
        ANNOTATIONS:json.dumps(ann,ensure_ascii=False,indent=2)+'\n'}


def main():
    for n,b in build().items():
        path=ROOT/n
        if path.exists():assert path.read_text(encoding='utf-8')==b,n
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(b)
    print('Source presentation now restricts a class of roles, not one role identity')


if __name__=='__main__':main()
