"""Check nonfactive ownership, completed care and same-judgment goodwill."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_reviewed_thoughts import (
    ROOT, LIBRARY, BASIS, PRIMITIVES, MEANINGS, parents, speech_entries,
    SPEECH_BASIS, SPEECH_DOC, build, closure)
from scripts.compose_qualitative_influence import TRUE
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

REPORT = 'reports/reviewed-thoughts-v1.json'
DOC = 'docs/reviewed-thoughts-v1.md'
EVIDENCE = 'data/reviewed-thoughts-lexical-v1.json'
PRIOR = 'reports/clerical-obligation-v1.json'
DOMAIN = ('person', 'thought', 'judgment', 'review', 'beneficiary', 'subject', 'aspect', 'second', 'other')
SCENES = ('past', 'now', 'future')
EXTRA = ''.join('r z' + n + '[] a.' for n in DOMAIN)
EXTRA += 'r znow[] d.r zcontent[a] e.r zalias[a] e.r zchoose[a i[h[a] e] i[h[a] e]] i[h[a] e].'
PROVIDER = 'd h224y[thought a] i[h[a] e][k zchoose[v thought r[p zcontent] r[p zalias]]].'


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(target='r36s', bindings=('person', 'thought')):
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, [target]), statements=[])
    prefix = parse('p:' + EXTRA + PROVIDER)
    provider = next(d for d in prefix['declarations'] if d['name'] == 'h224y')
    doc['declarations'] = [d for d in prefix['declarations'] if d['name'] != 'h224y'] + [
        deepcopy(provider if d['name'] == 'h224y' else d) for d in doc['declarations']]
    names = dict(r36m=('person','thought','judgment'), r36n=('person','thought','review'),
        r36p=('person','thought','review'), r36q=('person','thought','judgment'),
        r36r=('person','thought','judgment','beneficiary'), r36s=('person','thought','judgment','beneficiary'),
        r36t=('person','thought'))
    if target == 'r36o':
        seq = 'l[a][' + ' '.join('k z' + n + '[]' for n in bindings) + ']'
        call = 't[k r36o[' + seq + ']][k znow[]]'
    else:
        args = ' '.join('k z' + n + '[]' for n in names[target]) + ' k znow[]'
        if target == 'r36p': args += ' k znow[]'
        call = 'k ' + target + '[' + args + ']'
    return parse(format_graph(doc, 'compact') + 'q[' + call + '].')


def model(doc, variant='baseline'):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    for n in DOMAIN: v['z' + n] = lambda n=n: n
    v['znow'] = lambda: 'now'
    when = 'future' if variant == 'future_review' else 'now' if variant == 'current_review' else 'past'
    def matches(actual, expected, prefix, fields):
        return actual == tuple('other' if variant == prefix + '_' + f else e for e, f in zip(expected, fields))
    def owned(j, s, code, sign, at):
        return variant != 'unowned' and matches((j,s,symbol(code),sign,at),
            ('judgment','subject','zcontent',True,'now'), 'ownership', ('judgment','subject','code','sign','point'))
    def examined(j, s, code, at):
        syntax = json.loads(code.syntax)
        # rsb constructs an application of rsa to the exact content and TRUE.
        expected = dict(kind='apply', function=dict(kind='function_ref', symbol='rsa'),
            arguments=[dict(kind='function_ref', symbol='zcontent'),
                parse('p:q[' + TRUE + '].')['statements'][0]['body']])
        return syntax == expected and code.rank == 0 and matches((j,s,at),
            ('review','subject',when), 'examination', ('judgment','subject','point'))
    def goal(actor, act, code, bindings, at):
        fields = (actor,act,symbol(code),tuple(bindings.items),at)
        review = ('person','review','r36o',('person','thought'),when)
        good = ('person','judgment','rqym',('beneficiary',),'now')
        if variant == 'review_wrong_goal': review = (*review[:2], 'rqym', *review[3:])
        if variant == 'review_wrong_bindings': review = (*review[:3], ('thought','person'),when)
        if variant == 'goodwill_other_act': good = ('person','other',*good[2:])
        if variant == 'goodwill_wrong_beneficiary': good = (*good[:3], ('other',),'now')
        return fields in (review,good) and variant != ('no_review_aim' if act == 'review' else 'no_goodwill_aim')
    def attention(actor, act, code, bindings, aspect, at):
        return goal(actor,act,code,bindings,at) and (actor,act,at) == ('person','review',when) and aspect in (
            ('aspect',) if variant == 'missed_aspect' else ('aspect','second')) and variant != 'no_attention'
    def relevant(person, review, thought, aspect, reference):
        return variant != 'empty_aspects' and aspect in ('aspect','second') and matches(
            (person,review,thought,reference), ('person','review','thought','now'), 'scope', ('person','review','thought','reference'))
    def willing(actor, code, bindings, at):
        return variant != 'no_goodwill' and (actor,symbol(code),tuple(bindings.items),at) == ('person','rqym',('beneficiary',),'now')
    def history(person, anchor, at):
        return (person,anchor) == ('person','now') and at in (('now','future') if variant == 'foreign_history' else SCENES)
    def order(first,last,anchor):
        return anchor == 'now' and ((variant == 'cyclic' and (first,last) == ('now','past')) or SCENES.index(first) < SCENES.index(last))
    v.update(aa=lambda person: person == 'person',
        zchoose=lambda thought,first,second: first if thought == 'thought' and variant != 'different_content' else second,
        h224z=lambda thought: 'subject' if thought == 'thought' else 'other', hznn=owned, hzv=examined,
        fa=lambda person,j,at: matches((person,), ('person',), 'judge', ('person',)) and (j,at) in (('judgment','now'),('review',when)),
        fb=lambda j,s,at: s == 'subject' and (j,at) in (('judgment','now'),('review',when)),
        h246t=lambda review,at: variant != 'unfinished' and (review,at) == ('review',when),
        h246u=relevant, hztj=attention, hztl=goal, hzxq=willing, ia=history, ic=order,
        dg=lambda act,at: variant != 'no_occurrence' and (act,at) in (('review',when),('judgment','now')),
        df=lambda actor,act,at: variant != 'other_participant' and actor == 'person' and (act,at) in (('review',when),('judgment','now')))
    return v


@lru_cache(None)
def native_checks():
    rows = {}
    variants = ('baseline','current_review','future_review','unowned','unfinished','different_content',
        'ownership_judgment','ownership_subject','ownership_code','ownership_sign','ownership_point',
        'examination_judgment','examination_subject','examination_point','judge_person',
        'review_wrong_goal','review_wrong_bindings','goodwill_other_act','goodwill_wrong_beneficiary',
        'no_review_aim','no_goodwill_aim','missed_aspect','no_attention','empty_aspects',
        'scope_person','scope_review','scope_thought','scope_reference','no_goodwill','foreign_history','cyclic',
        'no_occurrence','other_participant')
    doc = fixture()
    for variant in variants:
        actual = evaluate(doc, model(doc,variant), DOMAIN, SCENES, True)
        assert actual == [variant in ('baseline','current_review')], (variant,actual)
        rows[variant] = actual[0]
    for truth in (False,True):
        v = model(doc); v.update(zcontent=lambda s: Content(SCENES,(truth,)*3), hzxp=lambda b,p: truth)
        assert evaluate(doc,v,DOMAIN,SCENES,True) == [True]
    assert evaluate(fixture('r36t'),model(fixture('r36t')),DOMAIN,SCENES,True) == [True]
    return dict(contrasts=rows, native_attention_and_goodwill_evaluated=True,
        content_truth_and_realized_benefit_not_required=True, unknown_content_not_executed=True)


@lru_cache(None)
def binding_checks():
    rows = {}
    for names in (('person','thought'), (), ('person',), ('thought','person'), ('person','thought','other'), ('person','other'), ('other','thought')):
        doc = fixture('r36o',names); v = model(doc,'current_review')
        actual = evaluate(doc,v,DOMAIN,SCENES,True)
        assert actual == [names == ('person','thought')], (names,actual)
        rows[str(names)] = actual[0]
    # Ownership, care and goodwill have independent countermodels.
    independent = {}
    for variant, expected in [('unowned',[False,True,False,False]),('unfinished',[True,False,False,True]),
        ('no_attention',[True,True,False,True]),('no_goodwill',[True,True,True,False])]:
        actual = [evaluate(fixture(t),model(fixture(t),variant),DOMAIN,SCENES,True)[0]
            for t in ('r36m','r36n','r36q','r36r')]
        # r36n is queried at now, while the default model reviews in the past.
        actual[1] = evaluate(fixture('r36n'), model(fixture('r36n'),variant) | {'znow': lambda:'past'},DOMAIN,SCENES,True)[0]
        assert actual == expected, (variant,actual)
        independent[variant] = actual
    return dict(exact_pair_bindings=rows, independent_ownership_review_and_care=independent)


@lru_cache(None)
def unknown_checks():
    doc = fixture(); rows = []
    for n in ('fa','fb','h224y','h224z','hznn','hzv','h246t','h246u','hztj','hztl','hzxq','dg','df','ia','ic'):
        if n == 'h224y': n = 'zchoose'
        v = model(doc); v[n] = unknown
        try: evaluate(doc,v,DOMAIN,SCENES,True)
        except ValueError as error: assert 'Unknown' in str(error), str(error)
        else: raise AssertionError(n)
        rows.append(n)
    return dict(unknown_relations_rejected=rows)


@lru_cache(None)
def structure_checks():
    new = catalog(); old = {n:e for p in parents() for n,e in p.entries.items()} | speech_entries()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration'] == old[n]['declaration'] and e['meaning_ja'] == old[n]['meaning_ja'],n
    for path,body in build().items(): assert (ROOT/path).read_text(encoding='utf-8') == body,path
    validate_hashes(ROOT, read(PRIOR)['source_sha256'])
    validate_hashes(ROOT, read(BASIS)['import_source_sha256'])
    for row in read(EVIDENCE)['sources']: assert digest((ROOT/row['raw_archive']).read_bytes()) == row['raw_sha256']
    for notation in ('compact','full'):
        text = format_graph(new.document,notation)
        assert parse(text) == parse(transcribe(text,alphabet='v2')) == new.document
    return dict(new_primitives=len(PRIMITIVES),new_definitions=len(MEANINGS),inherited_meanings_preserved=True,
        legacy_projection_unchanged=True,roundtrips=True,new_semantic_reviews=0)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items(): write_exact(ROOT/path,body)


def build_report():
    results = {}
    for name,fn in [('native',native_checks),('bindings',binding_checks),('unknown',unknown_checks),('structure',structure_checks)]:
        results[name] = fn(); print(name + ' checked',flush=True)
    paths = set(build()) | set().union(*(set(p.source_sha256) for p in parents())) | {SPEECH_BASIS,SPEECH_DOC,
        DOC,EVIDENCE,PRIOR,'scripts/compose_reviewed_thoughts.py','scripts/check_reviewed_thoughts.py',
        'tests/test_reviewed_thoughts.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    paths.update(row['raw_archive'] for row in read(EVIDENCE)['sources'])
    return dict(status='owned_completed_careful_review_and_benevolent_purpose',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
