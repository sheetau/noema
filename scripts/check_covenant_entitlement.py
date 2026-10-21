"""Check exact prospective formation, normative source, conflict and negative polarity."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_grounded_step import closure
from scripts.compose_covenant_entitlement import ROOT,LIBRARY,BASIS,NAMES,MEANINGS,parents,build
from scripts.compose_qualitative_influence import FALSE
from scripts.check_motive_causes import unknown,symbol
from scripts.check_pastoral_roles import evaluate

REPORT='reports/covenant-entitlement-v1.json'
DOC='docs/covenant-entitlement-v1.md'
READING='data/covenant-entitlement-reading-v1.json'
PRIORS=('reports/mediated-guardianship-v1.json','reports/classis-self-name-v1.json','reports/question-responses-v1.json')
DOMAIN=(*NAMES,'assessor','role','other')
SCENES=('reference','candidate','other')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r zt'+n+'[] d.' for n in SCENES)
BINDINGS='l[a]['+' '.join('k z'+n+'[]' for n in NAMES)+']'
PARAMS='k zassessor[] k zrole[] k zcommunity[] k ztreference[]'
NORM='k zassessor[] '+' '.join('k z'+n+'[]' for n in NAMES)+' k zrole[] k ztcandidate[]'


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
    v.update({'z'+n:lambda n=n:n for n in DOMAIN});v.update({'zt'+n:lambda n=n:n for n in SCENES})
    return v


def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)


@lru_cache(None)
def scope_checks():
    doc=fixture(('r47e','r47h'),'q[k r47e[k zbody[] k ztreference[]]].q[k r47h['+' '.join('k z'+n+'[]' for n in NAMES)+' k ztreference[]]].',('r456','r46c'))
    rows={}
    for clerical,delegated,religious in product((False,True),repeat=3):
        v=base(doc)
        v['r456']=lambda body,ref:clerical and (body,ref)==('body','reference')
        v['r46c']=lambda body,ref:delegated and (body,ref)==('body','reference')
        v['h245z']=lambda subject,ref:religious and (subject,ref)==('subject','reference')
        v['h246f']=lambda creed,subject,ref:(creed,subject,ref)==('creed','subject','reference')
        actual=run(doc,v);expected=[clerical or delegated,(clerical or delegated) and religious]
        assert actual==expected,(clerical,delegated,religious,actual);rows[str((clerical,delegated,religious))]=actual
    return dict(two_inclusive_routes_and_same_religious_confession=rows,
        boundaries='r456/r46c; pinned membership and church council validators remain unchanged',
        no_exclusive_choice_or_simultaneous_examples_required=True)


@lru_cache(None)
def binding_checks():
    rows={}
    for seq in (NAMES,NAMES[:-1],(*NAMES,'body'),tuple(reversed(NAMES))):
        literal='l[a]['+' '.join('k z'+n+'[]' for n in seq)+']'
        q=''.join('q[t[k r47f['+literal+']][k zt'+p+'[]]].' for p in ('reference','candidate'))
        doc=fixture(('r47f',),q,('r47d',));v=base(doc)
        v['h254z']=lambda agreement:'reference'
        v['r47d']=lambda *args:args==(*NAMES,'reference')
        actual=run(doc,v,NAMES);assert actual==[seq==NAMES]*2,(seq,actual);rows[str(seq)]=actual
    doc=fixture(('r47f',),'q[t[k r47f['+BINDINGS+']][k ztcandidate[]]].',('r47d',));v=base(doc)
    v['h254z']=lambda agreement:'other';v['r47d']=lambda *args:args==(*NAMES,'reference')
    assert run(doc,v,NAMES)==[False]
    return dict(exact_five_bindings_and_fixed_formation_anchor=rows,other_anchor_rejected=True,
        boundary='r47d; native purposeful oath formation checked in mediated-guardianship-v1')


def norm_model(doc,variant='baseline',permitted=True,forbidden=False):
    v=base(doc)
    def matches(assessor,body,role,code,bindings,sign,point,wanted):
        fields=['assessor','body','role','r47f',0,NAMES,wanted,'candidate']
        changes={'wrong_assessor':(0,'other'),'wrong_holder':(1,'other'),'wrong_role':(2,'other'),
                 'wrong_target':(3,'r47c'),'wrong_bindings':(5,tuple(reversed(NAMES))),
                 'wrong_polarity':(6,not wanted),'wrong_point':(7,'other')}
        if variant in changes:
            index,value=changes[variant];fields[index]=value
        if variant=='second_agreement':fields[5]=('body','other','creed','subject','community')
        return (assessor,body,role,symbol(code),code.rank,tuple(bindings.items),sign,point)==tuple(fields)
    v['h7l']=lambda *args:permitted and matches(*args,True)
    v['h7k']=lambda *args:forbidden and matches(*args,False)
    v['r456']=lambda body,ref:(body,ref)==('body','reference') and variant not in ('outside_scope','delegated_only')
    v['r46c']=lambda body,ref:(body,ref)==('body','reference') and variant=='delegated_only'
    v['h245z']=lambda subject,ref:(subject,ref)==('subject','reference')
    v['h246f']=lambda creed,subject,ref:(creed,subject,ref)==('creed','subject','reference') and variant!='other_creed'
    return v


@lru_cache(None)
def norm_checks():
    doc=fixture(('r47g',),'q[k r47g['+NORM+']].');rows={}
    for allowed,opposed in product((False,True),repeat=2):
        v=norm_model(doc,permitted=allowed,forbidden=opposed);actual=run(doc,v)
        assert actual==[allowed and not opposed],(allowed,opposed,actual);rows[str((allowed,opposed))]=actual[0]
        assert all(v[n] is unknown for n in ('h254z','h255a','h255f','h255l','h255k','dc'))
    for variant in ('wrong_assessor','wrong_holder','wrong_role','wrong_target','wrong_bindings','wrong_polarity','wrong_point'):
        actual=run(doc,norm_model(doc,variant));assert actual==[False],(variant,actual);rows[variant]=actual[0]
    for name in ('h7l','h7k'):
        v=norm_model(doc);v[name]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(native_conflict_free_positive_permission=rows,formation_goal_and_authority_not_executed=True,
        no_permission_not_physical_impossibility=True,unknown_not_denial=True)


@lru_cache(None)
def polarity_checks():
    q=('q[t[k r47i['+PARAMS+']][k ztcandidate[]]].q[t[k r47j['+PARAMS+']][k ztcandidate[]]].'
       'q[e[k r47k['+PARAMS+']][k r47l['+PARAMS+']]].'
       'q[e[k r47j['+PARAMS+']][k rii[k r47i['+PARAMS+'] '+FALSE+']]].')
    doc=fixture(('r47i','r47j','r47k','r47l'),q,('r456','r46c'));rows={}
    for variant in ('baseline','delegated_only','second_agreement','outside_scope','other_creed','wrong_target','wrong_holder','wrong_bindings'):
        v=norm_model(doc,variant);actual=run(doc,v)
        entitled=variant in ('baseline','delegated_only','second_agreement')
        assert actual==[entitled,not entitled,False,True],(variant,actual);rows[variant]=actual
    for allowed,opposed in product((False,True),repeat=2):
        actual=run(doc,norm_model(doc,permitted=allowed,forbidden=opposed));entitled=allowed and not opposed
        assert actual==[entitled,not entitled,False,True],(allowed,opposed,actual);rows[str((allowed,opposed))]=actual
    return dict(native_existential_candidate_and_same_negative_content=rows,
        question_and_assertion_have_distinct_force=True,negative_question_not_double_negated=True,
        second_agreement_prevents_false_universal_denial=True,
        boundaries='r456/r46c only; native scope, norm, quantification, signed messages are evaluated')


def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';unit=next(u for u in read(inv)['units'] if u['id']=='kant-1784:u0013')
    question=unit['text'][:409];answer='Ich sage: das ist ganz unmöglich.';start=unit['text'].index(answer)
    return dict(status='same_covenant_entitlement_and_negative_question_answer_dependency',source_inventory=inv,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],question_range=[0,409],question=question,answer_range=[start,start+len(answer)],answer=answer),
        primary_page=read('data/mediated-guardianship-reading-v1.json')['primary_page'],
        adopted_reading='正当な規範の下で、同じ永続的後見を目的とする不変信条への相互宣誓の合意を形成してよいという資格を問う。回答はこの資格事例の存在を否定する。目的の実現不能、全ての制度的効果の不存在、神的な権威の不存在を否定内容へ加えない。',
        general_scope='全成員が聖職者の団体と、長老も含み得る教会の職務代表団体という二つの構成を許す。教会会議とClassisはこの範囲で例示し、全員牧師条件をClassisへ押し付けない。',
        remaining=['第六段落固有の評価規範・立場・共同体・基準・提示文脈の供給','etwaの例示と二代替・自己呼称の提示',
                   'sogarの同じ目的の強調','Aberとsollte nichtの期待・反語的な問い','Ich sageとganzの著者帰属・全面的な拒否','本文統合と一文全体の判断'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)


@lru_cache(None)
def structure_checks():
    new=catalog();sources=parents()
    for n,e in new.entries.items():
        if n not in MEANINGS:
            old=next(c.entries[n] for c in sources if n in c.entries)
            assert e['declaration']==old['declaration'] and e['meaning_ja']==old['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for path in PRIORS:validate_hashes(ROOT,read(path)['source_sha256'])
    assert read(READING)==reading_record()
    page=read(READING)['primary_page'];assert digest((ROOT/page['path']).read_bytes())==page['sha256']
    assert not new.document['statements'] and len(sources[0].document['statements'])==96
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=0,
        no_new_author_assertion=True,same_source_question_and_answer_pinned=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)
    write_exact(ROOT/READING,json.dumps(reading_record(),ensure_ascii=False,indent=2)+'\n')


def build_report():
    results={}
    for name,fn in [('scope',scope_checks),('binding',binding_checks),('norm',norm_checks),('polarity',polarity_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    reading=read(READING)
    paths=set(build())|set(catalog().source_sha256)|set(PRIORS)|{DOC,READING,reading['source_inventory'],reading['primary_page']['path'],
        'scripts/compose_covenant_entitlement.py','scripts/check_covenant_entitlement.py','tests/test_covenant_entitlement.py',
        'scripts/check_motive_causes.py','scripts/check_pastoral_roles.py','scripts/compose_grounded_step.py',
        'scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py','scripts/compose_spiritual_guardians.py'}
    return dict(status='same_covenant_formation_entitlement_negative_question_and_answer',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
