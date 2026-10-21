"""Check reflexive customary naming without lexical truth or esteem inference."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_classis_self_name import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,parents,build,closure
from scripts.check_motive_causes import unknown,symbol
from scripts.check_pastoral_roles import evaluate
from scripts.fetch_classis_title_evidence import EVIDENCE,validate as validate_evidence

REPORT='reports/classis-self-name-v1.json'
DOC='docs/classis-self-name-v1.md'
READING='data/classis-self-name-reading-v1.json'
PRIORS=('reports/church-councils-v1.json',)
DOMAIN=('body','name','community','other')
SCENES=('reference','other')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+'r zref[] d.r zpoint[] d.'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(roots,query,boundaries=()):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    return parse(format_graph(doc,'compact')+EXTRA+query)


def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in DOMAIN});v.update(zref=lambda:'reference',zpoint=lambda:'other',h254u=lambda:'name',h254v=lambda:'community')
    return v


def run(doc,v):return evaluate(doc,v,DOMAIN,SCENES,True)


def model(doc,variant='baseline'):
    v=base(doc)
    v['hw2']=lambda name,code,ref:variant!='no_meaning' and (name,symbol(code),code.rank,ref)==(
        'other' if variant=='meaning_name' else 'name','r46k' if variant=='meaning_pattern' else 'r46l',
        1 if variant=='meaning_rank' else 0,'other' if variant=='meaning_reference' else 'reference')
    row=['body','body','name','community','reference']
    if variant.startswith('usage_'):
        i={'user':0,'target':1,'name':2,'community':3,'reference':4}[variant[6:]];row[i]='other'
    v['h254s']=lambda *args:variant!='no_use' and args==tuple(row)
    v['h254t']=lambda name,community,ref:variant!='no_honorific' and (name,community,ref)==(
        'other' if variant=='honorific_name' else 'name','other' if variant=='honorific_community' else 'community',
        'other' if variant=='honorific_reference' else 'reference')
    return v


@lru_cache(None)
def naming_checks():
    doc=fixture(('r46n',),'q[k r46n[k zbody[] k zname[] k zcommunity[] k zref[]]].')
    rows={}
    for variant in ('baseline','no_meaning','meaning_name','meaning_pattern','meaning_rank','meaning_reference',
        'no_use','usage_user','usage_target','usage_name','usage_community','usage_reference',
        'no_honorific','honorific_name','honorific_community','honorific_reference'):
        v=model(doc,variant);result=run(doc,v);assert result==[variant=='baseline'],(variant,result);rows[variant]=result[0]
        assert v['dg'] is unknown and v['h254m'] is unknown
    # Same object cannot be both the designation individual and its target.
    alias=fixture(('r46n',),'q[k r46n[k zbody[] k zbody[] k zcommunity[] k zref[]]].')
    v=base(alias);v['hw2']=lambda *a:True;v['h254s']=lambda *a:True;v['h254t']=lambda *a:True
    assert run(alias,v)==[False]
    for name in ('hw2','h254s','h254t'):
        v=model(doc);v[name]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(native_reflexive_naming_contrasts=rows,designation_not_target=True,
        no_execution_of_council_practice_or_hierarchy=True,unknown_not_false=True)


@lru_cache(None)
def classification_checks():
    doc=fixture(('r46o',),'q[k r46o[k zbody[] k zref[]]].',('r46k',))
    rows=[]
    for classified,named in product((False,True),repeat=2):
        v=model(doc);v['r46k']=lambda body,ref:classified and (body,ref)==('body','reference')
        if not named:v['h254s']=lambda *a:False
        result=run(doc,v);assert result==[classified and named];rows.append([classified,named,result[0]])
    for name in ('h254u','h254v'):
        v=model(doc);v['r46k']=lambda *a:True;v[name]=lambda:'other'
        assert run(doc,v)==[False]
    pattern=fixture(('r46l',),'q[t[k r46l[k zbody[]]][k zref[]]].q[t[k r46l[k zbody[]]][k zpoint[]]].',('r46k',))
    v=base(pattern);v['r46k']=lambda body,ref:(body,ref)==('body','reference')
    assert run(pattern,v)==[True,False]
    return dict(classification_naming_independent=rows,source_name_and_community_preserved=True,
        pattern_uses_same_body_and_content_reference=True,classification_boundary='r46k; pinned prior council report',
        self_name_does_not_establish_its_own_truth=True)


def reading_record():
    evidence=read(EVIDENCE);validate_evidence(evidence)
    primary=read('data/delegated-associations-evidence-v1.json')['source']
    text=primary['text']
    assert text[93:111]=='ehrwürdige Klassis'
    assert text[112:160]=='(wie sie sich unter den Holländern selbst nennt)'
    return dict(status='explicit_nominal_self_designation_not_whole_sentence_review',source=primary,
        designation=dict(symbol='h254u',range=[93,111],text=text[93:111]),
        parenthesis=dict(range=[112,160],text=text[112:160]),
        usage_community=dict(symbol='h254v',range=[136,146],text=text[136:146]),
        institutional_content=dict(symbol='r46l',basis='data/church-councils-basis-v1.json',root='r46k'),
        evidence=EVIDENCE,evidence_sha256=digest((ROOT/EVIDENCE).read_bytes()),
        interpretation=[
            '括弧内は敬称付きの名辞全体を自己呼称として説明すると読む。名称の保持する制度的な性質と、名称の敬称形式を別関係で結ぶ。',
            '使用主体と呼称対象を同じ会議体へ固定する。著者や第三者だけによる呼び方では代用しない。用法共同体をネーデルラントの人々として固定し、個別の会議の所在地や成員全員の国籍を付け足さない。',
            'ehrwürdigを慣習的な敬意の形式として保持する。著者の内心の敬愛や反語を事実として決めず、会議体の正当性を呼称から導かない。',
        ],remaining=['etwaと一般団体への例示','問い全体と後続の否定回答','誓約・不変信条・上位後見・持続'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)


@lru_cache(None)
def structure_checks():
    new=catalog();old=parents()
    for n,e in new.entries.items():
        if n not in MEANINGS and n not in PRIMITIVES:
            previous=next(c.entries[n] for c in old if n in c.entries)
            assert e['declaration']==previous['declaration'] and e['meaning_ja']==previous['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for notation in ('compact','full'):
        body=format_graph(new.document,notation);assert parse(body)==parse(transcribe(body,alphabet='v2'))==new.document
    for path in PRIORS:validate_hashes(ROOT,read(path)['source_sha256'])
    assert read(READING)==reading_record()
    assert not new.document['statements'] and len(old[0].document['statements'])==96
    return dict(unchanged_imports=True,roundtrips=True,source_ranges_and_archival_evidence_pinned=True,
        new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),no_new_source_sentence=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)
    write_exact(ROOT/READING,json.dumps(reading_record(),ensure_ascii=False,indent=2)+'\n')


def build_report():
    results={}
    for name,fn in [('naming',naming_checks),('classification',classification_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    evidence=read(EVIDENCE)
    paths=set(build())|set(catalog().source_sha256)|set(PRIORS)|{DOC,READING,EVIDENCE,evidence['path'],
        'data/delegated-associations-evidence-v1.json','artifacts/written-units-v1/kant-1784.json',
        'scripts/compose_classis_self_name.py','scripts/check_classis_self_name.py','tests/test_classis_self_name.py',
        'scripts/fetch_classis_title_evidence.py','scripts/check_motive_causes.py','scripts/check_pastoral_roles.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='same_regional_council_and_customary_honorific_self_name',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
