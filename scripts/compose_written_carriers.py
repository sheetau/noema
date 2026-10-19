"""Explain externally readable works through bound records and carriers."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT,closure

PARENT='examples/v016/kant-role-qualifications.noema'
PARENT_BASIS='data/role-qualifications-basis-v1.json'
FULL='examples/v016/kant-written-carriers.noema'
CORE='examples/v016/written-carriers-core.noema'
LIBRARY='examples/v016/recorded-work-carriers.noema'
BASIS='data/written-carriers-basis-v1.json'
ANNOTATIONS='data/written-carriers-identifiers-v1.json'
PRIMITIVES={
 'hzwr':(['record','work','scene'],'その記録は、その状況で、指定された作品の記された表現を実現する記録である。同じ話題への言及や要約だけを、その作品の記録として補わない。作品として採る単位と版の範囲は解釈で固定し、別の作品の記録と混同しない。内容の真理や、読者の理解を要求しない。'),
 'hzws':(['record','carrier','scene'],'その状況で、その同じ記録が、記憶内の像だけではない外部の媒体に、後から参照できる持続する痕跡として保持されている。媒体への言及や、現在は消失した記録の過去の所在とは区別する。紙・印刷・製本など特定の材質や技法には限定しない。'),
 'hzwt':(['record','scene'],'その状況で、その記録の表現を適切な読み取り方によって識別し参照できる。現在の特定の読者が手元に持つこと、当該言語を理解すること、全内容への理解や賛同は要求しない。破壊・消失して読めない痕跡を読めるものとして補わない。'),
}
MEANINGS={
 'rqxk':'指定した作品と媒体の間に、その同じ作品を実現し、その同じ媒体に保持され、その同じ状況で参照可能な記録が存在する。三関係の記録を共有する。作品に一つの媒体しかないこと、媒体に一作品しかないこと、作品と写しの同一性は導かない。',
 'sd':'作品を実現する参照可能な記録が、少なくとも一つの持続する外部媒体に保持される。rqxkで作品・記録・媒体・状況を結ぶ。作品の内容と複製媒体を区別し、特定の人による所持・理解・利用は要求しない。',
 'sl':'一つにまとめた記された作品scであり、作品を実現する記録が外部媒体に保持され参照できるsdを満たす。書物を内容として利用するこの例の部分説明であり、作品と写しの同一性、物理的な製本様式、他の記された作品から書物を区別する全条件は含めない。',
}

@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)

def build():
    old=parent();doc=deepcopy(old.document)
    assert not (set(PRIMITIVES)|{'rqxk'})&set(old.entries)
    at=next(i for i,d in enumerate(doc['declarations']) if d['name']=='sd')
    prefix=deepcopy(doc);prefix.update(declarations=doc['declarations'][:at],statements=[])
    text='''r hzwr[a a d] c.r hzws[a a d] c.r hzwt[a d] c.
d rqxk[work a carrier a scene d records h[a a d] c carries h[a a d] c readable h[a d] c] c[
 g record a[w[c[v records][v record v work v scene]][w[c[v carries][v record v carrier v scene]][c[v readable][v record v scene]]]]
].
d sd[work a scene d] c[g carrier a[k rqxk[v work v carrier v scene p hzwr p hzws p hzwt]]].'''
    parsed=parse(format_graph(prefix,'compact')+text)
    doc['declarations']=parsed['declarations']+doc['declarations'][at+1:]
    doc=parse(format_graph(doc,'compact'))
    basis=dict(status='external_readability_composed_from_records_and_carriers',document=FULL,
        revises_document=PARENT,revises_meaning_basis=PARENT_BASIS,primitives={},definitions={},
        predecessor_source_sha256=old.source_sha256,
        limitations=['sdを基本関係から構成的な定義へ変更する。作品の単位・版・表現の一般的な基礎説明は残る。',
            '書物と他の記された作品の語義上の区別、宗教上の助言者・良心・第二段落全体は未完。',
            '同じ作品の複数媒体と、一媒体上の複数作品を許すが、媒体や記録の個数を原文へ補わない。'],
        unresolved=[dict(basis=r['basis'],historical_caveats=r['caveats']) for r in old.lineage])
    for d in doc['declarations']:
        n=d['name']
        if d['kind']=='primitive':
            labels,meaning=PRIMITIVES[n] if n in PRIMITIVES else (old.entries[n]['arguments'],old.entries[n]['meaning_ja'])
            basis['primitives'][n]=dict(parameters=d['parameters'],result=d['result'],arguments=labels,meaning_ja=meaning)
        else:basis['definitions'][n]=MEANINGS[n] if n in MEANINGS else old.entries[n]['meaning_ja']
    core=deepcopy(doc);core['statements']=[doc['statements'][4]]
    core['declarations']=closure(doc,_references(core['statements']))
    lib=deepcopy(doc);lib.update(declarations=closure(doc,['rqxk']),statements=[])
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/role-qualifications-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

def main():
    from scripts.audit_opening_scope import write_exact
    for p,s in build().items():write_exact(ROOT/p,s)
    print('Written works connected to records and carriers',flush=True)

if __name__=='__main__':main()
