"""Check rank, command direction, signed content, and absence of truth export."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_officer_command_binding import ROOT, LIBRARY, BASIS, PRIMITIVES, MEANINGS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

REPORT = 'reports/officer-command-binding-v1.json'
DOC = 'docs/officer-command-binding-v1.md'
EVIDENCE = 'data/officer-example-evidence-v1.json'
PRIOR = ('reports/role-commands-v1.json', 'reports/scholarly-compatibility-v1.json')
DOMAIN = ('person','issuer','office','higher','middle','institution','otherinstitution','notice','action','other')
SCENES = ('reference','other')
EXTRA = ''.join('r z'+n+'[] a.' for n in ('person','issuer','office','higher','institution','notice','action','other'))+'r zref[] d.'


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(kind, sign=True, bindings=('person','action')):
    roots={'message':['r32j'], 'officer':['r32k'], 'hierarchy':['r32l'], 'delivery':['r32m'], 'bound':['r32n']}[kind]
    doc=deepcopy(catalog().document)
    doc.update(declarations=closure(doc,roots),statements=[])
    polarity='e[k zperson[]][k zperson[]]' if sign else 'u[e[k zperson[]][k zperson[]]]'
    args={
        'message':'l[a]['+' '.join('k z'+n+'[]' for n in bindings)+'] '+polarity,
        'officer':'k zperson[] k zoffice[] k zinstitution[] k zref[]',
        'hierarchy':'k zissuer[] k zperson[] k zhigher[] k zoffice[] k zinstitution[] k zref[]',
        'delivery':'k zissuer[] k zperson[] k znotice[] k zaction[] '+polarity+' k zref[]',
        'bound':'k zperson[] k zoffice[] k zinstitution[] k zissuer[] k zhigher[] k znotice[] k zaction[] '+polarity+' k zref[]',
    }[kind]
    marker='l' if kind=='message' else 'q'
    return parse(format_graph(doc,'compact')+EXTRA+marker+'[k '+roots[0]+'['+args+']].')


def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    for n in ('person','issuer','office','higher','institution','notice','action','other'):
        v['z'+n]=lambda n=n:n
    v['zref']=lambda:'reference'
    return v


@lru_cache(None)
def message_checks():
    rows=[]
    for sign,executed in product((False,True),repeat=2):
        doc=fixture('message',sign);v=base(doc)
        v['cg']=lambda p,a,s: executed and (p,a,s)==('person','action','reference')
        actual=evaluate(doc,v,DOMAIN,SCENES,True)[0]
        assert actual.force=='direct'
        assert actual.content.situations==SCENES
        assert actual.content.values==(executed==sign,False==sign)
        rows.append(dict(polarity=sign,executed=executed,content=list(actual.content.values)))
    adapters={}
    for bindings in ((),('person',),('person','action'),('action','person'),('person','action','other')):
        for sign in (False,True):
            doc=fixture('message',sign,bindings);v=base(doc)
            v['cg']=lambda p,a,s:(p,a,s)==('person','action','reference')
            actual=evaluate(doc,v,DOMAIN,SCENES,True)[0]
            valid=len(bindings)==2
            wanted=(valid and ((bindings==('person','action'))==sign),valid and not sign)
            assert actual.content.values==wanted,(bindings,sign,actual)
            adapters[str((bindings,sign))]=list(actual.content.values)
    return dict(signed_execution=rows,bindings=adapters,command_force_composed=True,
                invalid_length_does_not_vacuously_satisfy_negative_command=True)


def model(doc,variant='baseline',sign=True):
    v=base(doc)
    holders={('person','office'),('issuer','higher')}
    appointments={('person','office','institution'),('issuer','higher','institution')}
    entrusted=set(holders)
    roles={'office','higher','middle'}
    edges={('higher','office')}
    if variant=='other_officer_role':
        holders.discard(('person','office'));holders.add(('person','middle'))
    if variant=='other_officer_institution':
        appointments.discard(('person','office','institution'));appointments.add(('person','office','otherinstitution'))
    if variant=='other_superior_institution':
        appointments.discard(('issuer','higher','institution'));appointments.add(('issuer','higher','otherinstitution'))
    if variant=='unentrusted_office': entrusted.discard(('person','office'))
    if variant=='unentrusted_superior': entrusted.discard(('issuer','higher'))
    if variant=='outside_role': roles.discard('higher')
    if variant=='reversed_rank': edges={('office','higher')}
    if variant=='reflexive_rank': edges.add(('office','office'))
    if variant=='cyclic_rank': edges.add(('office','higher'))
    if variant=='nontransitive_rank': edges.add(('office','middle'))
    if variant=='same_person':
        v['zissuer']=lambda:'person'
        holders.add(('person','higher'));appointments.add(('person','higher','institution'));entrusted.add(('person','higher'))
    v.update(aa=lambda p:p in ('person','issuer'),
        hzwn=lambda p,r,s:(p,r) in holders and s=='reference',
        hzxf=lambda p,r,i,s:(p,r,i) in appointments and s=='reference',
        cf=lambda p,r,s:(p,r) in entrusted and s=='reference',
        h233d=lambda i,s:variant!='not_military' and (i,s)==('institution','reference'),
        h233e=lambda r,i,s:variant!='not_officer_rank' and (r,i,s)==('office','institution','reference'),
        h242w=lambda r,i,s:r in roles and (i,s)==('institution','reference'),
        h242x=lambda hi,lo,i,s:(hi,lo) in edges and (i,s)==('institution','reference'),
        dg=lambda notice,s:variant!='not_issued' and (notice,s)==('notice','reference'),
        f3=lambda issuer,notice,s:(issuer,notice,s)==(
            'other' if variant=='other_presenter' else 'issuer',
            'other' if variant=='other_presentation_event' else 'notice','reference'))
    def presents(notice,recipient,bindings,polarity,code,point):
        return (notice,recipient,tuple(bindings.items),polarity,symbol(code),code.rank,point)==(
            'notice','other' if variant=='other_recipient' else 'person',
            ('other' if variant=='other_commanded_person' else 'person',
             'other' if variant=='other_commanded_action' else 'action'),
            not sign if variant=='wrong_polarity' else sign,'r32j',0,
            'other' if variant=='other_presentation_reference' else 'reference')
    v['h242v']=presents
    return v


@lru_cache(None)
def officer_checks():
    doc,rows=fixture('officer'),{}
    for variant in ('baseline','other_officer_role','other_officer_institution','unentrusted_office','not_military','not_officer_rank'):
        actual=evaluate(doc,model(doc,variant),DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual)
        rows[variant]=actual[0]
    return dict(contrasts=rows,same_appointed_office_and_institution=True)


@lru_cache(None)
def hierarchy_checks():
    doc,rows=fixture('hierarchy'),{}
    for variant in ('baseline','other_superior_institution','outside_role','reversed_rank','reflexive_rank',
                    'cyclic_rank','nontransitive_rank','same_person','unentrusted_superior'):
        actual=evaluate(doc,model(doc,variant),DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual)
        rows[variant]=actual[0]
    return dict(contrasts=rows,native_rez_rey_rex_order_evaluated=True,
                hierarchy_does_not_imply_command_or_legitimacy=True)


@lru_cache(None)
def delivery_checks():
    rows={}
    for sign in (False,True):
        doc=fixture('delivery',sign)
        for variant in ('baseline','not_issued','other_presenter','other_presentation_event','other_recipient',
                        'other_commanded_person','other_commanded_action','wrong_polarity','other_presentation_reference'):
            v=model(doc,variant,sign)
            assert v['cg'] is unknown
            actual=evaluate(doc,v,DOMAIN,SCENES,True)
            assert actual==[variant=='baseline'],(sign,variant,actual)
            rows[str((sign,variant))]=actual[0]
    return dict(contrasts=rows,command_execution_not_evaluated=True,
                receipt_understanding_and_normative_validity_not_inferred=True)


@lru_cache(None)
def bound_checks():
    doc,rows=fixture('bound'),{}
    for variant in ('baseline','other_officer_role','other_superior_institution','other_presenter',
                    'other_commanded_person','other_commanded_action','wrong_polarity'):
        actual=evaluate(doc,model(doc,variant),DOMAIN,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual)
        rows[variant]=actual[0]
    for name in ('hzxf','h242w','h242x','dg','f3','h242v'):
        v=model(doc);v[name]=unknown
        try: evaluate(doc,v,DOMAIN,SCENES,True)
        except ValueError as error: assert 'Unknown' in str(error)
        else: raise AssertionError(name)
    return dict(contrasts=rows,native_institution_and_delivery_composed=True,unknown_inputs_refused=6)


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    assert not new.document['statements']
    for n,e in new.entries.items():
        if n not in MEANINGS and n not in PRIMITIVES:
            assert e['declaration']==old.entries[n]['declaration'],n
            assert e['meaning_ja']==old.entries[n]['meaning_ja'],n
    for path in PRIOR: validate_hashes(ROOT,read(path)['source_sha256'])
    for path,body in build().items(): assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for notation in ('compact','full'):
        text=format_graph(new.document,notation)
        assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    evidence=read(EVIDENCE)
    assert [p['page'] for p in evidence['pages']]==[485,486]
    for p in evidence['pages']: assert digest((ROOT/p['path']).read_bytes())==p['sha256']
    unit=next(u for u in read('artifacts/written-units-v1/kant-1784.json')['units'] if u['id']==evidence['source']['unit'])
    assert unit['text_sha256']==evidence['source']['unit_sha256']
    a,b=evidence['source']['range'];assert unit['text'][a:b]==evidence['source']['text']
    return dict(new_definitions=5,new_primitives=3,new_semantic_reviews=0,
                unchanged_active_manuscript=True,source_pages_pinned=True,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items(): write_exact(ROOT/path,body)


def build_report():
    results={}
    for name,fn in [('message',message_checks),('officer',officer_checks),('hierarchy',hierarchy_checks),
                    ('delivery',delivery_checks),('bound',bound_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(parent().source_sha256)|{
        DOC,EVIDENCE,*PRIOR,'artifacts/written-units-v1/kant-1784.json',
        'scripts/compose_officer_command_binding.py','scripts/check_officer_command_binding.py','tests/test_officer_command_binding.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    paths.update(p['path'] for p in read(EVIDENCE)['pages'])
    return dict(status='officer_superior_and_addressed_command_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
