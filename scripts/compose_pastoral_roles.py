"""Connect a provider to a role whose principal function is spiritual care."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT,closure

PARENT='examples/v016/kant-written-carriers.noema'
PARENT_BASIS='data/written-carriers-basis-v1.json'
FULL='examples/v016/kant-pastoral-roles.noema'
CORE='examples/v016/pastoral-roles-core.noema'
LIBRARY='examples/v016/principal-service-roles.noema'
BASIS='data/pastoral-roles-basis-v1.json'
ANNOTATIONS='data/pastoral-roles-identifiers-v1.json'
PRIMARY_MEANING='その実践の役割において、記述された受け手の活動への判断・指示・援助が、主要な務めの一つである。単に付随的に行い得ること、最近もっとも頻繁に行ったこと、本人の好みや実際の成功とは別の関係。主要性は同じ実践・役割・状況における位置付けであり、唯一の務めや数値的な時間割合を要求しない。'
MEANINGS={
 'rqxl':'同じ主体・役割・状況について、その主体が役割を持ち、同じ役割が指定活動への援助機能を持ち、その同じ機能が主要な務めである。一つの役割の保持と別の役割の主要な機能を混ぜない。現在の実行、成功、能力や資格充足は要求しない。',
 'rqxm':'人であり、他者について宗教的な生き方・安寧に関する判断soを援助する継続的な役割・実践siを担う。旧spの広い援助者の条件を保存する。社会的な役割での主要な務めという条件はまだ含まない。',
 'sp':'rqxmの宗教上の継続的な援助者であり、その同じ本人が持つ社会的な役割で、soへの援助が主要な務めの一つである。Seelsorgerの歴史的な職務上の読みへの部分説明。特定教派の叙任手続、教義の真理、本人の信仰や仕事の成功は追加しない。宗教的な配慮を判断への援助で表すことの範囲、聖職者の制度的な全条件は未確認。',
}

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)

def build():
    old=parent();doc=deepcopy(old.document)
    assert not {'rqxl','rqxm','hzwu'}&set(old.entries)
    moved=[deepcopy(old.entries[n]['declaration']) for n in ('hzwn','hzwo')]
    doc['declarations']=[d for d in doc['declarations'] if d['name'] not in ('hzwn','hzwo')]
    at=next(i for i,d in enumerate(doc['declarations']) if d['name']=='sp')
    prefix=deepcopy(doc);prefix.update(declarations=doc['declarations'][:at]+moved,statements=[])
    raw=deepcopy(old.entries['sp']['declaration']);raw['name']='rqxm';prefix['declarations'].append(raw)
    text='''r hzwu[a i[h[a] e] d] c.
d rqxl[person a task i[h[a] e] scene d holds h[a a d] c serves h[a i[h[a] e] d] c principal h[a i[h[a] e] d] c] c[
 g role a[w[c[v holds][v person v role v scene]][w[c[v serves][v role v task v scene]][c[v principal][v role v task v scene]]]]
].
d sp[person a scene d] c[w[k rqxm[v person v scene]][k rqxl[v person r[p so] v scene p hzwn p hzwo p hzwu]]].'''
    parsed=parse(format_graph(prefix,'compact')+text)
    doc['declarations']=parsed['declarations']+doc['declarations'][at+1:]
    doc=parse(format_graph(doc,'compact'))
    basis=dict(status='principal_pastoral_role_function',document=FULL,revises_document=PARENT,
        revises_meaning_basis=PARENT_BASIS,primitives={},definitions={},predecessor_source_sha256=old.source_sha256,
        limitations=['歴史辞典の主要な務めという記述を役割へ接続する。カントの唯一の語義や聖職者の制度全体を確定する変更ではない。',
            '宗教的な配慮を判断の援助で表す範囲、良心、書物の全語義、第二段落全体は未完。'],
        unresolved=[dict(basis=r['basis'],historical_caveats=r['caveats']) for r in old.lineage])
    for d in doc['declarations']:
        n=d['name']
        if d['kind']=='primitive':
            labels,meaning=(['role','recipient_activity_description','scene'],PRIMARY_MEANING) if n=='hzwu' else (old.entries[n]['arguments'],old.entries[n]['meaning_ja'])
            basis['primitives'][n]=dict(parameters=d['parameters'],result=d['result'],arguments=labels,meaning_ja=meaning)
        else:basis['definitions'][n]=MEANINGS[n] if n in MEANINGS else old.entries[n]['meaning_ja']
    core=deepcopy(doc);core['statements']=[doc['statements'][4]]
    core['declarations']=closure(doc,_references(core['statements']))
    lib=deepcopy(doc);lib.update(declarations=closure(doc,['rqxl']),statements=[])
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/written-carriers-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

def main():
    from scripts.audit_opening_scope import write_exact
    for p,s in build().items():write_exact(ROOT/p,s)
    print('Principal pastoral role composed',flush=True)

if __name__=='__main__':main()
