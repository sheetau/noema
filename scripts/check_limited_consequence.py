"""Check activity-scoped exclusion, concessive cases, and nonfactive attribution."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, canonical_digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_limited_consequence import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, LIMITS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_attributed_focus import unwrap
from scripts.check_uncertain_judgment import source_values as judgment_values, PEOPLE as JUDGMENT_PEOPLE, SCENES as JUDGMENT_SCENES

INDEX = 'data/semantic-review-index-v110.json'
REPORT = 'reports/limited-consequence-v1.json'
AUDIT = 'data/limited-consequence-reading-v1.json'
DOC = 'docs/limited-consequence-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = ['reports/minimum-challenge-v1.json', 'reports/unfamiliar-judgment-v1.json', 'reports/uncertain-judgment-v1.json', 'reports/abandoned-reliance-v1.json', 'reports/depicted-referents-v1.json', 'reports/fetters-sentence-v1.json']
SENTENCES = [('data/nature-sentence-reading-v1.json', [51]), ('data/confirmed-incapacity-reading-v1.json', [11, 12]), ('data/fetters-sentence-reading-v1.json', [10, 52])]
PEOPLE = ('person', 'second', 'act', 'other', 'author', 'node', 'topic', 'harder', 'hardest')
SCENES = ('anchor', 'one', 'two', 'expected')


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))
@lru_cache(None)
def document(): return parse((ROOT / FULL).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


def fixture(roots, extra):
    doc = deepcopy(document()); doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + extra)


def unknowns(doc): return {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}


def refuse(doc, values, names, people=PEOPLE, scenes=SCENES):
    for name in names:
        changed = dict(values); changed[name] = unknown
        try: evaluate(doc, changed, people, scenes, True)
        except ValueError as error: assert 'Unknown' in str(error), (name, str(error))
        else: raise AssertionError(name)


def substitute(doc, roots, primitives, replacements):
    probes = parse('p:' + primitives + replacements)
    mapped = {d['name']: d for d in probes['declarations'] if d['kind'] != 'primitive'}
    doc['declarations'] = [d for d in probes['declarations'] if d['kind'] == 'primitive'] + [deepcopy(mapped.get(d['name'], d)) for d in doc['declarations']]
    doc['declarations'] = closure(doc, roots)
    return parse(format_graph(doc, 'compact'))


@lru_cache(None)
def exclusion_checks():
    doc = fixture(['r2ia'], 'r zitem[] a.r zpoint[] d.r zfocus[a d] c.r zfirst[a d] c.r zsecond[a d] c.'+
        'q[k r2ia[k zitem[] k zpoint[] p zfocus l[h[a d] c][p zfirst p zsecond]]].'+
        'q[k r2ia[k zitem[] k zpoint[] p zfocus l[h[a d] c][]]].')
    def model(bits=(True, False, False)):
        return dict(zitem=lambda: 'act', zpoint=lambda: 'anchor', **{n:(lambda item, point, b=b: b and (item, point)==('act', 'anchor')) for n,b in zip(('zfocus','zfirst','zsecond'),bits)})
    for bits in product((False, True), repeat=3):
        assert evaluate(doc, model(bits), PEOPLE, SCENES, True) == [bits[0] and not any(bits[1:]), False]
    values = model(); values['zfirst'] = lambda item, point: (item, point) in (('other', 'anchor'), ('act', 'two'))
    assert evaluate(doc, values, PEOPLE, SCENES, True) == [True, False]
    refuse(doc, model(), ('zfocus', 'zfirst', 'zsecond'))
    return dict(combinations=8, empty_alternatives_refused=True, other_item_and_point_not_excluded=True,
        unknown_inputs_refused=3, expectation_not_required=True)


@lru_cache(None)
def profile_checks():
    doc = fixture(['r2ha','r2ic','r2id','r2ie','r2hb'], 'r zperson[] a.r zact[] a.r ztopic[] a.r zanchor[] d.'+
        ''.join('q[k '+name+'[k zperson[] k zact[] k ztopic[] k zanchor[]]].' for name in ('r2ha','r2ic','r2id'))+
        ''.join('q[t[k '+name+'[k zperson[]]][k zanchor[]]].' for name in ('r2ie','r2hb')))
    for actual, first, second in product((False, True), repeat=3):
        uncertain = not (first and second)
        assert evaluate(doc, judgment_values(doc, actual_support=actual, responses=(first,second)), JUDGMENT_PEOPLE, JUDGMENT_SCENES, True) == [uncertain, not uncertain, uncertain, uncertain, uncertain]
    rows = {}
    for name in ('no_actual','empty_profile','missing_counterpart','changed_basis','no_opportunity','cycle','guided_actual','wrong_actual_faculty'):
        actual = evaluate(doc, judgment_values(doc, name), JUDGMENT_PEOPLE, JUDGMENT_SCENES, True)
        assert actual == [False]*5, (name,actual); rows[name] = actual
    # The shared comparison inputs must be exact, not a second independently chosen profile.
    decls = {d['name']: d for d in document()['declarations']}
    a,b = decls['r2gz']['body'],decls['r2ib']['body']
    assert a['arguments'] == b['arguments'] and (a['symbol'],b['symbol']) == ('r2gw','r2gv')
    return dict(combinations=8, cases=rows, same_profile_arguments=True,
        actual_reason_support_not_excluded=True, limitation_does_not_strengthen_prior_uncertainty=True)


@lru_cache(None)
def concession_checks():
    roots = ['r2ig','zperson','zanchor']
    doc = fixture(['r2ig'], 'r zperson[] a.r zanchor[] d.q[t[k r2ig[k zperson[]]][k zanchor[]]].')
    doc = substitute(doc, roots, 'r zp[a d] c.r zq[a d] c.',
        'd r2gt[person a] e[b point[k zp[v person v point]]].d r2hb[person a] e[b point[k zq[v person v point]]].')
    def model(bits=(True, True, False, False), variant='baseline'):
        return dict(zperson=lambda:'person', zanchor=lambda:'anchor', wa=lambda:'author',
            zp=lambda p,s: p=='person' and s in ('one','two') and bits[('one','two').index(s)],
            zq=lambda p,s: p=='person' and s in ('one','two') and bits[2+('one','two').index(s)],
            ke=lambda author,p,d,sc,s: variant!='empty' and (author,p,symbol(d),sc)==(
                'other' if variant=='wrong_author' else 'author', 'other' if variant=='wrong_person' else 'person',
                'r2hb' if variant=='wrong_description' else 'r2gt', 'two' if variant=='wrong_context' else 'anchor') and s in ('one','two'))
    for bits in product((False,True),repeat=4):
        assert evaluate(doc,model(bits),PEOPLE,SCENES,True)==[all(bits[:2]) and not any(bits[2:])]
    rows={}
    for name in ('baseline','empty','wrong_author','wrong_person','wrong_description','wrong_context'):
        actual=evaluate(doc,model(variant=name),PEOPLE,SCENES,True);assert actual==[name=='baseline'];rows[name]=actual
    refuse(doc,model(),('ke','zp','zq','wa'))
    return dict(combinations=16,cases=rows,unknown_inputs_refused=4,
        actual_premise_and_outcome_not_asserted=True, same_person_description_and_context=True,
        nonempty_candidates_must_satisfy_premise=True)


def package_document():
    roots=['r2im','rsx','rsy','rsw','wh']
    suffix=''.join('q[k '+operation+'['+package+' k wh[]]].' for package in ('k r2im[]','k rsw[k r2im[]]') for operation in ('rsx','rsy'))
    doc=fixture(roots,suffix)
    pairs=[('r2gt','ante'),('r2hj','causal'),('r2ie','limited'),('r2hb','uncertain')]
    return substitute(doc,roots,''.join('r z'+name+'[a d] c.' for _,name in pairs),
        ''.join('d '+name+'[person a] e[b point[k z'+primitive+'[v person v point]]].' for name,primitive in pairs))


def package_values(doc, causal=(True,True), scalar=(True,True), concessive=(True,True), variant='baseline'):
    from scripts.check_minimum_challenge import boundary_values
    values=boundary_values(doc,causal,scalar,variant)
    people=('person','second')
    values.update(zlimited=lambda p,s:p in people and s=='one' and not (variant=='missing_limitation' and p=='second'),
        zante=lambda p,s:p in people and (s=='expected' or variant!='no_departure' and s=='one'),
        zuncertain=lambda p,s:p in people and (s=='one' or s=='expected' and not concessive[people.index(p)]),
        ke=lambda author,p,d,context,s: (author,symbol(d),context,s)==('author','r2gt','one','expected') and p in people)
    return values


@lru_cache(None)
def package_checks():
    doc=package_document()
    for bits in product((False,True),repeat=6):
        fg=all(bits[:2]);bg=all(bits[2:])
        actual=evaluate(doc,package_values(doc,bits[:2],bits[2:4],bits[4:]),PEOPLE,SCENES,True)
        assert actual==[fg,bg,not fg,bg],(bits,actual)
    rows={}
    for name,expected in [('baseline',[True,True,False,True]),('missing_limitation',[False,True,True,True]),
        ('empty_people',[False,False,True,False]),('empty_cases',[False,False,True,False]),('no_departure',[False,False,True,False]),
        ('wrong_case',[False,True,True,True]),('wrong_task',[False,False,True,False])]:
        actual=evaluate(doc,package_values(doc,variant=name),PEOPLE,SCENES,True)
        assert actual==expected,(name,actual);rows[name]=actual
    return dict(combinations=64,cases=rows,content_boundary_test=True,
        scalar_and_concessive_inputs_independent=True,negation_preserves_both_backgrounds=True,
        same_two_people_and_their_tasks=True)


@lru_cache(None)
def attribution_checks():
    doc=fixture(['r2in'], 'q[k r2in[]].')
    doc=substitute(doc,['r2in'],'r zreference[] c.','d r2gi[] c[k zreference[]].')
    fg=dict(kind='call',symbol='r2ik',arguments=[]);bg=dict(kind='call',symbol='r2il',arguments=[])
    def model(variant='baseline'):
        values=unknowns(doc)
        values.update(h3s=lambda:'reason',h3a=lambda:'clause',wa=lambda:'author',wh=lambda:'anchor',
            zreference=lambda:variant!='missing_reference',
            ue=lambda a,b,s:variant!='wrong_order' and (a,b,s)==('clause','reason','anchor'),
            hznreport=lambda node,author,content,scope,sc:variant!='missing_claim' and (node,author,scope,sc)==('reason','author','reason','anchor') and unwrap(content)==fg,
            hzrbgreport=lambda node,author,f,b,fs,bs,sc:variant!='missing_background' and (node,author,fs,bs,sc)==('reason','author','reason','clause','anchor') and unwrap(f)==fg and unwrap(b)==bg)
        if variant=='wrong_author':values['wa']=lambda:'other'
        if variant=='wrong_node':values['h3s']=lambda:'other'
        return values
    rows={}
    for name in ('baseline','missing_reference','wrong_order','missing_claim','missing_background','wrong_author','wrong_node'):
        actual=evaluate(doc,model(name),PEOPLE+('clause','reason'),SCENES,True)
        assert actual==[name=='baseline'],(name,actual);rows[name]=actual
    refuse(doc,model(),('zreference','ue','hznreport','hzrbgreport'),PEOPLE+('clause','reason'))
    return dict(cases=rows,reference_boundary_test=True,quoted_content_not_executed=True,
        exact_foreground_background_and_scopes=True,unknown_inputs_refused=4)


@lru_cache(None)
def quotation_checks():
    doc=fixture(['r2im','rsu','rsv','rsw'],
        'q[e[k rsu[k r2im[]]][r c[k r2ik[]]]].q[e[k rsv[k r2im[]]][r c[k r2il[]]]].'+
        'q[e[k rsv[k rsw[k r2im[]]]][r c[k r2il[]]]].')
    assert evaluate(doc,unknowns(doc),PEOPLE,SCENES,True)==[True]*3
    return dict(closed_package_without_world_evaluation=True,exact_foreground_and_background_quotes=True)


def native_values(doc, variant):
    values = judgment_values(doc, variant, responses=(True, variant == 'reliable'))
    old_fa, old_dg = values['fa'], values['dg']
    values.update(h2d=lambda: 'source', wa=lambda: 'author', zpast=lambda: 'before', zcopy=lambda: 'copy',
        fa=lambda p, j, s: old_fa(p, j, s) or (p, j, s) == ('person', 'copy', 'before'),
        hzzzm=lambda n, a, d, p, o, s: (n, a, symbol(d), p, o, s) == ('source', 'author', 'r2fh', 'person', 'topic', 'anchor'),
        hzzzo=lambda sc, o, p, a, s: (sc, o, p) == ('anchor', 'topic', 'person') and (a, s) in (('before', 'one'), ('anchor', 'two')),
        hzzzp=lambda *args: True, hzzzq=lambda *args: True, hzzzr=lambda *args: False,
        hx2=lambda p, o, act, s: (p, o, act, s) == ('person', 'topic', 'act', 'one'), hz2=lambda *args: False,
        dg=lambda act, s: old_dg(act, s) or (act, s) in (('act', 'one'), ('copy', 'before')) or variant != 'no_departure' and (act, s) == ('process', 'anchor'),
        hzzzs=lambda p, end, t: (p, end) == ('person', 'anchor') and t in ('before', 'anchor') and not (variant == 'missing_history' and t == 'anchor'),
        ic=lambda a, b, s: (a, b, s) == ('before', 'anchor', 'anchor'),
        ag=lambda proc, a, b: (proc, a, b) == ('process', 'before', 'anchor'),
        la=lambda p, proc, a, b: (p, proc, a, b) == ('person', 'process', 'before', 'anchor'),
        df=lambda p, proc, s: (p, proc, s) == ('person', 'process', 'anchor'),
        hzid=lambda p, proc, old, new, a, b: (p, proc, symbol(old), symbol(new), a, b) == ('person', 'process', 'r2gp', 'r2gq', 'before', 'anchor'),
        g3=lambda proc, p, d, s: (proc, p, symbol(d), s) == ('process', 'person', 'r2gq', 'anchor'),
        hzzzy=lambda p, sc, s: (p, sc, s) == ('person', 'anchor', 'anchor'),
        h3e=lambda p, event, d, s: (p, event, symbol(d), s) == ('person', 'copy', 'r2hf', 'before'),
        h3g=lambda event, p, d, a, b: (event, p, symbol(d), a, b) == ('copy', 'person', 'r2hf', 'before', 'anchor'),
        h3f=lambda p, d, s: variant == 'familiar' and (p, symbol(d), s) == ('person', 'r2hf', 'anchor'),
        hzie=lambda p, f, q, e, s: variant != 'no_cause' and (p, symbol(f), q, symbol(e), s) == (
            'person', 'r2hf' if variant == 'wrong_description' else 'r2hh', 'person', 'r2hb', 'anchor'),
        ea=lambda *args: variant != 'adoption_absent')
    tasks = ('topic', 'harder', 'hardest')
    levels = (1, 0, 2) if variant == 'not_minimum' else (0, 0, 0) if variant == 'all_tied' else (0, 1, 2)
    values.update(
        h222a=lambda p, sc, t: variant != 'empty_scope' and (p, sc) == ('person', 'anchor') and t in tasks,
        h222b=lambda p, a, b, s: (p, s) == ('person', 'anchor') and a in tasks and b in tasks and levels[tasks.index(a)] <= levels[tasks.index(b)],
        h222c=lambda observer, pred, a, t, b, u, s: (observer, symbol(pred), a, b, s) == (
            'author', 'r2hb' if variant == 'wrong_predicate' else 'r2hn', 'person',
            'other' if variant == 'wrong_actor' else 'person', 'anchor') and t in tasks and u in tasks and (
                t == u or variant != 'no_expectation' and tasks.index(t) > tasks.index(u)))
    # A second departure history belongs to the normal expectation world 'one'.
    # It keeps the same fixed referents and has its own end point.
    prior = dict(values)
    values.update(
        hzzzs=lambda p,end,t: prior['hzzzs'](p,end,t) or (p,end)==('person','one') and t in ('before','one'),
        ic=lambda a,b,s: prior['ic'](a,b,s) or (a,b,s)==('before','one','one'),
        hzzzo=lambda sc,o,p,a,s: prior['hzzzo'](sc,o,p,a,s) or (sc,o,p,a,s)==('anchor','topic','person','one','two'),
        ag=lambda proc,a,b: prior['ag'](proc,a,b) or (proc,a,b)==('process','before','one'),
        la=lambda p,proc,a,b: prior['la'](p,proc,a,b) or (p,proc,a,b)==('person','process','before','one'),
        df=lambda p,proc,s: prior['df'](p,proc,s) or (p,proc,s)==('person','process','one'),
        dg=lambda act,s: prior['dg'](act,s) or (act,s)==('process','one'),
        hzid=lambda p,proc,old,new,a,b: prior['hzid'](p,proc,old,new,a,b) or (p,proc,symbol(old),symbol(new),a,b)==('person','process','r2gp','r2gq','before','one'),
        g3=lambda proc,p,d,s: prior['g3'](proc,p,d,s) or (proc,p,symbol(d),s)==('process','person','r2gq','one'),
        ke=lambda author,p,d,sc,s: variant!='concession_empty' and (author,p,symbol(d),sc,s)==(
            'author','other' if variant=='concession_wrong_person' else 'person',
            'r2hb' if variant=='concession_wrong_description' else 'r2gt','anchor',
            'anchor' if variant=='actual_as_normal' else 'two' if variant=='false_normal_premise' else 'one'))
    return values


def add_reliable_activity(values):
    old = dict(values)
    performed = lambda p,j,s: p=='person' and (j=='secure' and s=='anchor' or j=='securecopy' and s in ('one','two'))
    values.update(
        fa=lambda p,j,s:old['fa'](p,j,s) or performed(p,j,s),
        dg=lambda j,s:old['dg'](j,s) or performed('person',j,s),
        fb=lambda j,t,s:old['fb'](j,t,s) or j in ('secure','securecopy') and t=='topic',
        ac=lambda p,f,j,s:old['ac'](p,f,j,s) or (p,f)==('person','faculty') and j in ('secure','securecopy'),
        fc=lambda j,r,s:old['fc'](j,r,s) or j in ('secure','securecopy') and r=='reason',
        fd=lambda r,j,s:old['fd'](r,j,s) or r=='reason' and j in ('secure','securecopy'),
        hzzzt=lambda p,j,t,a,s:old['hzzzt'](p,j,t,a,s) or (p,j,t,a)==('person','secure','topic','anchor') and s in ('one','two'),
        hzzzx=lambda p,j,t,a,s,c:old['hzzzx'](p,j,t,a,s,c) or (p,j,t,a,c)==('person','secure','topic','anchor','securecopy') and s in ('one','two'))


@lru_cache(None)
def native_checks():
    doc=fixture(['r2ii','r2ij','r2hv','r2ig','r2ie','r2hb','r2ic'], 'r zperson[] a.r zanchor[] d.r zsecure[] a.r ztopic[] a.'+
        ''.join('q[t[k '+name+'[k zperson[]]][k zanchor[]]].' for name in ('r2ii','r2ij','r2hv','r2ig','r2ie','r2hb'))+
        'q[k r2ic[k zperson[] k zsecure[] k ztopic[] k zanchor[]]].')
    people=JUDGMENT_PEOPLE+('process','source','author','harder','hardest','secure','securecopy')
    scenes=('before','anchor','one','two')
    rows={}
    for variant in ('baseline','familiar','no_cause','no_actual','no_departure','not_minimum','no_expectation','all_tied',
        'concession_empty','concession_wrong_person','concession_wrong_description','actual_as_normal','false_normal_premise','other_reliable_activity'):
        values=native_values(doc,variant);values['zsecure']=lambda:'secure';values['ztopic']=lambda:'topic'
        if variant=='other_reliable_activity':add_reliable_activity(values)
        limited=variant!='no_actual'
        foreground=variant not in ('familiar','no_cause','no_actual','no_departure','not_minimum')
        concession=variant not in ('concession_empty','concession_wrong_person','concession_wrong_description','actual_as_normal','false_normal_premise')
        background=concession and variant not in ('no_departure','not_minimum','no_expectation','all_tied')
        wanted=[foreground,background,foreground,concession,limited,limited,variant=='other_reliable_activity']
        actual=evaluate(doc,values,people,scenes,True)
        assert actual==wanted,(variant,actual,wanted);rows[variant]=actual
    return dict(cases=rows,native_departure_cause_limitation_and_two_backgrounds_executed=True,
        actual_and_normal_departure_histories_executed=True,other_reliable_activity_allowed=True,
        prior_causal_description_unchanged=True,prior_uncertainty_and_limited_content_agree=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0010')
    phrase = 'würde dennoch auch über den schmalesten Graben einen nur unsicheren Sprung thun'
    start = unit['text'].index(phrase, 474); end = start + len(phrase)
    current = catalog(); dependencies = [d['name'] for d in closure(current.document, ['r2in'])]
    paths = {INDEX, INVENTORY, FULL, BASIS, PARENT, PARENT_BASIS, *PRIOR, *(p for p, _ in SENTENCES)}
    return dict(status='unasserted_limited_consequence_and_concession_candidate', reviewer='assistant_review', document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[start, end], text=unit['text'][start:end]),
        candidate_definitions=list(MEANINGS), candidate_dependency_sha256=canonical_digest([current.entries[n] for n in dependencies]),
        candidate_dependencies=dependencies, preserved_authored_selection=selection_binding(current, [13, 53]),
        decision='同じ活動内の確実性の代替を排除する限定と、同じ離脱を認めた通常候補での帰結不成立による譲歩を接続し、前景・背景・参照を保つ非事実的な帰属候補を構成する。身体描写との全対応と第四文全体の読解判断は未完。',
        interpretation_limits=LIMITS, revised_statement_indices=[],
        references=[dict(url='https://korpora.org/Kant/aa08/036.html', title='Kant AA VIII036', accessed='2026-10-20',
            use='主節のdennochとnur unsicherenを照合。同じ活動の確かな遂行を対照にする限定と、通常予想に反する帰結の読みを候補として明示し、全能力の欠如へ拡張しない。')],
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_verified_sentence_characters=0, preserved_reviewed_sentence_characters=408,
        semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['declarations'][:-14] == old.document['declarations']
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    assert len(new.document['statements']) == 54 and old.document['statements'] == new.document['statements']
    for path in read(INDEX)['works']['kant-1784']['reviews']:
        record = read(path); validate_hashes(ROOT, record['source_sha256'])
        indices = [s['index'] for s in record['selection']['statements']]
        assert record['selection'] == selection_binding(old, indices) == selection_binding(new, indices)
    for path, indices in SENTENCES:
        record = read(path); validate_hashes(ROOT, record['source_sha256'])
        assert record['selection'] == selection_binding(new, indices)
    for path in PRIOR: validate_hashes(ROOT, read(path)['source_sha256'])
    assert not set(MEANINGS) & set(selection_binding(new, list(range(54)))['dependencies'])
    for path, body in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for path in (FULL, CORE, LIBRARY):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for style in ('compact', 'full'):
            text = format_graph(doc, style); assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    assert read(AUDIT) == reading()
    return dict(added_definitions=14, added_primitives=0, authored_statements=54, preserved_statements=54,
        revised_statement_indices=[], preserved_review_selections=12, reviewed_nonblank_characters=2212,
        preserved_reviewed_sentence_characters=408, candidate_not_asserted=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items(): write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('exclusion', exclusion_checks), ('profile', profile_checks), ('concession', concession_checks),
                     ('package', package_checks), ('native', native_checks), ('attribution', attribution_checks),
                     ('quotation', quotation_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    record = reading()
    paths = set(build()) | set(catalog().source_sha256) | set(record['source_sha256']) | {
        AUDIT, DOC, 'scripts/compose_limited_consequence.py', 'scripts/check_limited_consequence.py',
        'scripts/register_limited_consequence.py', 'tests/test_limited_consequence.py',
        'scripts/check_minimum_challenge.py', 'scripts/check_attributed_focus.py', 'scripts/check_uncertain_judgment.py', 'scripts/check_abandoned_reliance.py', 'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    for path in PRIOR: paths.update(read(path)['source_sha256'])
    paths.update(read(INDEX)['works']['kant-1784']['reviews'])
    return dict(status='limited_consequence_and_concession_candidate_checked', document=FULL, **results,
        alignment=dict(**record['source'], definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_covered_characters=0, new_verified_sentence_characters=0, preserved_reviewed_sentence_characters=408,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})


if __name__ == '__main__':
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT / REPORT, encoded(build_report()))
