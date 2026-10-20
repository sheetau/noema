"""Check fixed-content conviction and the scope of hypothetical negation."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_personal_conviction import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,parent,build
from scripts.check_motive_causes import unknown,symbol
from scripts.check_pastoral_roles import evaluate
from scripts.check_teaching_discretion import extract

DOC='docs/personal-conviction-v1.md'
REPORT='reports/personal-conviction-v1.json'
EVIDENCE='data/personal-conviction-evidence-v1.json'
PRIOR='reports/clerical-report-forecast-v1.json'
DOMAIN=('person','target','j1','j2','other')
SCENES=('reference','actual','p1','p2','p3','other')
CANDIDATES=('p1','p2','p3')
EXTRA='''r zperson[] a.r ztarget[] a.r zjudgment[] a.
r zreference[] d.r zactual[] d.r zpoint[] d.
r ztruth[a d d] c.r zcondition[d] c.r zshown[i b[c]] c.
d zcontent[target a reference d] e[b point[k ztruth[v target v reference v point]]].
d zalias[target a reference d] e[k zcontent[v target v reference]].
d zpremise[point d] c[k zcondition[v point]].
d zpremisealias[point d] c[k zpremise[v point]].'''
ARGS='k zperson[] k ztarget[] r[p zcontent] k zreference[]'
JARGS='k zperson[] k zjudgment[] k ztarget[] r[p zcontent] k zreference[] k zpoint[]'
NEGATIVE='k r42g['+ARGS+' r[p zpremise] k zactual[]]'
POSITIVE='k r42f[k zperson[] r[p zpremise] i[point d][k r42e['+ARGS+' v point]] k zactual[]]'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(query=None):
    doc=deepcopy(catalog().document);doc['statements']=[]
    if query is None:
        query='q[k r42c['+JARGS+']].q[k r42d['+JARGS+']].q[k r42e['+ARGS+' k zpoint[]]].'
    return parse(format_graph(doc,'compact')+EXTRA+query)


def model(doc,bits=(True,True,True),selected=CANDIDATES,full=CANDIDATES,
          premise=SCENES,variant='baseline',vary_judgment=False):
    owns,affirms,conviction=bits
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update(zperson=lambda:'person',ztarget=lambda:'target',zjudgment=lambda:'j1',
        zreference=lambda:'reference',zactual=lambda:'actual',zpoint=lambda:'p1',zcondition=lambda at:at in premise)
    def judgment(at):return 'j2' if vary_judgment and at=='p2' else 'j1'
    def match(actual,expected,category,fields):
        expected=list(expected)
        for i,field in enumerate(fields):
            if variant==category+'_'+field:expected[i]='other'
        return tuple(actual)==tuple(expected)
    v['fa']=lambda p,j,at:owns and match((p,j,at),('person',judgment(at),at),
        'owner',('person','judgment','point'))
    v['h245q']=lambda j,t,c,ref,pol,at:affirms and match((j,t,ref,at),(judgment(at),'target','reference',at),
        'affirmation',('judgment','target','reference','point')) and pol==(variant!='negative_polarity') and c.rank==0 and symbol(c)==(
            'zalias' if variant=='content_alias' else 'zcontent')
    v['h252d']=lambda j,at:conviction and at in full and match((j,at),(judgment(at),at),'conviction',('judgment','point'))
    v['hzko']=lambda p,c,actual,at:at in selected and match((p,actual),('person','actual'),'selection',('person','actual')) and c.rank==0 and symbol(c)==(
        'zpremisealias' if variant=='premise_alias' else 'zpremise')
    return v


def run(doc,v):return evaluate(doc,v,DOMAIN,SCENES,True)


@lru_cache(None)
def conviction_checks():
    doc=fixture();rows=[]
    for bits in product((False,True),repeat=3):
        result=run(doc,model(doc,bits));expected=[all(bits[:2]),all(bits),all(bits)]
        assert result==expected,(bits,result);rows.append(dict(bits=bits,result=result))
    # A confident judgment cannot supply conviction for a different affirmative judgment.
    v=model(doc);v['h252d']=lambda j,at:j=='j2'
    assert run(doc,v)==[True,False,False]
    # An additional unrelated judgment must not invalidate the matching witness.
    v=model(doc);v['h252d']=lambda j,at:j in ('j1','j2')
    assert run(doc,v)==[True,True,True]
    return dict(truth_table=rows,same_judgment_required=True,extra_judgments_allowed=True,
        affirmation_without_full_conviction_allowed=True,content_truth_and_objective_justification_not_executed=True)


@lru_cache(None)
def modal_checks():
    doc=fixture('q['+POSITIVE+'].q['+NEGATIVE+'].q[u['+POSITIVE+']].');rows=[]
    for bits in product((False,True),repeat=6):
        selected=tuple(p for p,b in zip(CANDIDATES,bits[:3]) if b)
        full=tuple(p for p,b in zip(CANDIDATES,bits[3:]) if b)
        pos=bool(selected) and set(selected)<=set(full)
        neg=bool(selected) and not set(selected)&set(full)
        result=run(doc,model(doc,selected=selected,full=full))
        assert result==[pos,neg,not pos],(bits,result)
        rows.append(dict(selected=selected,fully_convinced_at=full,result=result))
    for actual_premise in (False,True):
        premise=CANDIDATES+(('actual',) if actual_premise else ())
        assert run(doc,model(doc,full=(),premise=premise))==[False,True,True]
    assert run(doc,model(doc,full=(),premise=('p1','p3')))==[False,False,True]
    assert run(doc,model(doc,selected=(),full=()))==[False,False,True]
    # An affirmative judgment without full conviction is enough to reject the
    # mistaken inference from "would not fully endorse" to "would not affirm".
    v=model(doc,full=());assert run(doc,v)==[False,True,True]
    local=fixture();assert run(local,model(local,full=()))==[True,False,False]
    # The universal modal is outside the existential judgment, allowing the
    # same content to be affirmed by different judgments in different cases.
    assert run(doc,model(doc,vary_judgment=True))==[True,False,False]
    # Actual-world conviction is independent of the selected hypothetical cases.
    for full in ((),('actual',)):
        assert run(doc,model(doc,full=full))==[False,True,True]
    return dict(selection_and_conviction_cases=rows,actual_premise_need_not_be_false=True,
        invalid_selected_premise_refused=True,empty_selection_is_not_counterfactual_success=True,
        would_not_distinct_from_not_would=True,negation_not_plain_disagreement=True,
        judgment_witness_may_vary_by_candidate=True,actual_conviction_independent=True)


@lru_cache(None)
def reference_checks():
    doc=fixture();rows={}
    for category,fields in [('owner',('person','judgment','point')),
            ('affirmation',('judgment','target','reference','point')),('conviction',('judgment','point'))]:
        for field in fields:
            variant=category+'_'+field;result=run(doc,model(doc,variant=variant))
            expected=[True,False,False] if category=='conviction' else [False]*3
            assert result==expected,(variant,result);rows[variant]=result
    for variant in ('content_alias','negative_polarity'):
        result=run(doc,model(doc,variant=variant));assert result==[False]*3;rows[variant]=result
    modal=fixture('q['+POSITIVE+'].q['+NEGATIVE+'].')
    for variant in ('selection_person','selection_actual','premise_alias'):
        result=run(modal,model(modal,variant=variant,full=()))
        assert result==[False,False],(variant,result);rows[variant]=result
    for name in ('fa','h245q','h252d','hzko','zcondition'):
        v=model(modal);v[name]=unknown
        try:run(modal,v)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,unknown_inputs_not_treated_as_absence=True,
        fixed_reference_not_replaced_by_candidate=True,syntax_preserved=True)


@lru_cache(None)
def quotation_checks():
    quoted='r b['+NEGATIVE+']'
    shown=fixture('q[k zshown['+quoted+']].')
    v={d['name']:unknown for d in shown['declarations'] if d['kind']=='primitive'}
    seen=[]
    def record(code):seen.append((code.rank,json.loads(code.syntax)));return code.rank==1
    v['zshown']=record
    assert run(shown,v)==[True] and seen[0][1]['symbol']=='r42g'
    actual=fixture('q[s['+quoted+']].')
    assert run(actual,model(actual,full=()))==[True]
    assert run(actual,model(actual))==[False]
    return dict(closed_rank_one_quotation=True,quotation_does_not_execute=True,
        exact_quoted_body_evaluated=True,no_asserted_source_sentence=True)


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for notation in ('compact','full'):
        text=format_graph(new.document,notation)
        assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for page in read(EVIDENCE)['pages']:
        raw=(ROOT/page['path']).read_bytes()
        assert digest(raw)==page['sha256'] and page['excerpt'] in extract(raw.decode(page['encoding']))
    validate_hashes(ROOT,read(PRIOR)['source_sha256'])
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        no_source_sentence_added=True,lexical_evidence_pinned=True,technical_conviction_reading_not_claimed=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    result={name:fn() for name,fn in [('conviction',conviction_checks),('modal',modal_checks),
        ('references',reference_checks),('quotation',quotation_checks),('structure',structure_checks)]}
    paths=set(build())|set(catalog().source_sha256)|{DOC,EVIDENCE,PRIOR,
        'scripts/compose_personal_conviction.py','scripts/check_personal_conviction.py','tests/test_personal_conviction.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_teaching_discretion.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    paths.update(p['path'] for p in read(EVIDENCE)['pages'])
    return dict(status='personal_conviction_and_hypothetical_nonendorsement',document=LIBRARY,**result,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
