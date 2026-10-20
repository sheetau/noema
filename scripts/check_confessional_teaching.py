"""Check adopted code identity, nonfactive profession and actual exposition."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_confessional_teaching import (
    ROOT, LIBRARY, BASIS, NAMES, PRIMITIVES, MEANINGS, STANDARD, MESSAGE, CRITERIA, CRITERION,
    parents, build, closure)
from scripts.check_clerical_audiences import model as audience_model, DOMAIN as AUDIENCE_DOMAIN
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

REPORT = 'reports/confessional-teaching-v1.json'
DOC = 'docs/confessional-teaching-v1.md'
PRIOR = ('reports/clerical-audiences-v1.json', 'reports/public-civic-opinion-v1.json')
EVIDENCE = 'data/clerical-teaching-lexical-v1.json'
DOMAIN = (*AUDIENCE_DOMAIN, 'creed', 'standard', 'activity')
SCENES = ('reference', 'outcome', 'other')
EXTRA = ''.join('r z' + n + '[] a.' for n in DOMAIN) + 'r zref[] d.r zpoint[] d.'
EXTRA += 'r zbelief[] e.r zotherbelief[] e.r zmeaning[a] e.d zmessage[subject a] f[j s[k zmeaning[v subject]]].'
EXTRA += 'r zjudge[a ' + MESSAGE + '] e.r zpass[a ' + MESSAGE + '] e.'
EXTRA += 'r zconditions[' + CRITERIA + ' ' + CRITERIA + '] ' + CRITERIA + '.'
EXTRA += 'd zcriteria[] ' + CRITERIA + '[k zconditions[l[' + CRITERION + '][p zpass p zjudge] l[' + CRITERION + '][]]].'
EXTRA += 'd zaliascriteria[] ' + CRITERIA + '[k zcriteria[]].'
EXTRA += 'r zchoosebelief[a d i[e] i[e]] i[e].r zchoosestandard[a d ' + STANDARD + ' ' + STANDARD + '] ' + STANDARD + '.'
PROVIDERS = '''
d h246e[formulation a reference d] i[e][k zchoosebelief[v formulation v reference r[k zbelief[]] r[k zotherbelief[]]]].
''' + 'd h246j[standard a reference d] ' + STANDARD + '[k zchoosestandard[v standard v reference r[k zcriteria[]] r[k zaliascriteria[]]]].'


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(target):
    doc = deepcopy(catalog().document); doc.update(declarations=closure(doc, [target]), statements=[])
    prefix = parse('p:' + EXTRA + PROVIDERS)
    providers = {d['name']: d for d in prefix['declarations'] if d['name'] in ('h246e', 'h246j')}
    doc['declarations'] = [d for d in prefix['declarations'] if d['name'] not in providers] + [
        deepcopy(providers.get(d['name'], d)) for d in doc['declarations']]
    names = dict(r35r=('church', 'creed', 'subject'), r35s=('church', 'creed', 'subject', 'standard'),
        r35t=NAMES, r35u=NAMES, r35v=NAMES)[target]
    args = ' '.join('k z' + n + '[]' for n in names) + ' k zref[]'
    if target in ('r35u', 'r35v'): args += ' k zactivity[]'
    if target == 'r35u': args += ' r[p zmessage]'
    call = 'k ' + target + '[' + args + ']'
    if target in ('r35u', 'r35v'): call = 't[' + call + '][k zpoint[]]'
    return parse(format_graph(doc, 'compact') + 'q[' + call + '].')


def base(doc):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    for n in DOMAIN: v['z' + n] = lambda n=n: n
    v.update(zref=lambda: 'reference', zpoint=lambda: 'outcome')
    return v


def model(doc, variant='baseline'):
    v = base(doc)
    v.update({n: f for n, f in audience_model(doc, variant).items() if f is not unknown})
    def matches(actual, expected, fields):
        return actual == tuple('other' if variant == f else e for e, f in zip(expected, fields))
    def belief(formulation, ref, first, second):
        return first if matches((formulation, ref), ('creed', 'reference'), ('provider_creed', 'provider_reference')) else second
    def standard(rule, ref, first, second):
        return first if variant != 'equivalent_alias' and matches((rule, ref), ('standard', 'reference'),
            ('provider_standard', 'standard_reference')) else second
    def adoption(church, creed, standard, code, point):
        points = ('outcome',) if variant == 'no_reference_adoption' else ('reference',) if variant == 'no_current_adoption' else SCENES
        return point in points and matches((church, creed, standard, symbol(code), code.rank),
            ('church', 'creed', 'standard', 'zcriteria', 0),
            ('adopting_church', 'adopted_creed', 'adopted_standard', 'adopted_description', 'adopted_rank'))
    def criterion(subject, code):
        if variant == 'unknown_criterion': return unknown()
        same = matches((subject, symbol(code), code.rank), ('subject', 'zmessage', 0),
            ('criterion_subject', 'criterion_message', 'criterion_rank'))
        return Content(SCENES, tuple(same and not (variant == 'criterion_failed' and point == 'outcome') for point in SCENES))
    v.update(zchoosebelief=belief, zchoosestandard=standard,
        zconditions=lambda full, empty: empty if variant == 'empty_criteria' else full,
        zjudge=criterion, zpass=lambda subject, code: Content(SCENES, (True,) * len(SCENES)),
        h246d=lambda church, ref: variant != 'not_organization' and matches((church, ref), ('church', 'reference'),
            ('organization_church', 'organization_reference')),
        h246f=lambda creed, subject, ref: variant != 'not_profession' and matches((creed, subject, ref),
            ('creed', 'subject', 'reference'), ('profession_creed', 'profession_subject', 'profession_reference')),
        h246g=lambda church, creed, code, ref: matches((church, creed, symbol(code), code.rank, ref),
            ('church', 'creed', 'zbelief', 0, 'reference'), ('avowal_church', 'avowal_creed', 'avowal_content', 'avowal_rank', 'avowal_reference')),
        h246h=lambda church, code, ref: matches((church, symbol(code), code.rank, ref),
            ('church', 'hzxi', 0, 'reference'), ('practice_church', 'practice_description', 'practice_rank', 'practice_reference')),
        h246i=adoption,
        h246k=lambda person, church, role, point: point in (('reference',) if variant == 'no_current_service' else SCENES) and
            matches((person, church, role), ('person', 'church', 'role'), ('serving_person', 'served_church', 'service_role')),
        h246l=lambda person, activity, subject, code, point: variant != 'not_exposition' and matches(
            (person, activity, subject, symbol(code), code.rank, point), ('person', 'activity', 'subject', 'zmessage', 0, 'outcome'),
            ('expositor', 'exposition_activity', 'exposition_subject', 'exposition_message', 'exposition_rank', 'exposition_point')),
        cb=lambda person, act, role, point: matches((person, act, role, point), ('person', 'activity', 'role', 'outcome'),
            ('position_person', 'position_activity', 'position_role', 'position_point')),
        cf=lambda person, role, point: variant != 'not_entrusted' and (person, role, point) == ('person', 'role', 'outcome'),
        dg=lambda act, point: variant != 'no_event' and (act, point) == ('activity', 'outcome'),
        f3=lambda person, act, point: (person, act, point) == ('other' if variant == 'other_presenter' else 'person', 'activity', 'outcome'))
    def presentation(act, recipient, subject, code, point):
        recipients = ('learner', 'member') if variant == 'missing_overlap' else ('learner', 'overlap') if variant == 'missing_member' else ('learner', 'member', 'overlap')
        return recipient in recipients and matches((act, subject, symbol(code), code.rank, point),
            ('activity', 'subject', 'zmessage', 0, 'outcome'),
            ('presentation_activity', 'presentation_subject', 'presentation_message', 'presentation_rank', 'presentation_point'))
    v['f2'] = presentation
    return v


@lru_cache(None)
def profession_checks():
    doc, rows = fixture('r35r'), {}
    for variant in ('baseline', 'not_organization', 'organization_church', 'organization_reference', 'not_profession',
        'profession_creed', 'profession_subject', 'profession_reference', 'nonreligious_subject',
        'provider_creed', 'provider_reference', 'avowal_church', 'avowal_creed', 'avowal_content', 'avowal_reference',
        'practice_church', 'practice_description', 'practice_reference'):
        v = model(doc, variant); v['dg'] = unknown
        assert v['zbelief'] is unknown and v['dg'] is unknown
        actual = evaluate(doc, v, DOMAIN, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual); rows[variant] = actual[0]
    return dict(contrasts=rows, native_same_profession_and_institution=True,
        creed_truth_and_religious_practice_not_evaluated=True)


@lru_cache(None)
def standard_checks():
    doc, rows = fixture('r35s'), {}
    for variant in ('baseline', 'provider_standard', 'standard_reference', 'equivalent_alias', 'adopting_church',
        'adopted_creed', 'adopted_standard', 'adopted_description', 'no_reference_adoption'):
        v = model(doc, variant); v['zjudge'] = unknown; v['zconditions'] = unknown
        actual = evaluate(doc, v, DOMAIN, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual); rows[variant] = actual[0]
    return dict(contrasts=rows, same_adopted_closed_criteria_description=True,
        extensionally_equal_alias_not_substituted=True, adoption_does_not_execute_criteria=True)


@lru_cache(None)
def teaching_checks():
    doc, rows = fixture('r35u'), {}
    for variant in ('baseline', 'empty_criteria', 'criterion_failed', 'criterion_subject', 'criterion_message',
        'not_organization', 'equivalent_alias', 'adopted_creed', 'adopted_standard', 'no_reference_adoption',
        'no_current_adoption', 'no_current_service', 'served_church', 'service_role', 'not_exposition',
        'expositor', 'exposition_activity', 'exposition_subject', 'exposition_message', 'exposition_point',
        'position_role', 'not_entrusted', 'no_event', 'other_presenter', 'missing_overlap', 'missing_member',
        'presentation_activity', 'presentation_subject', 'presentation_message', 'presentation_point',
        'pupil_teacher', 'care_church', 'extra_pupil', 'empty'):
        v = model(doc, variant)
        assert v['zbelief'] is unknown and v['zmeaning'] is unknown
        actual = evaluate(doc, v, DOMAIN, SCENES, True)
        assert actual == [variant in ('baseline', 'empty_criteria')], (variant, actual); rows[variant] = actual[0]
    return dict(contrasts=rows, native_rfw_rfv_rfu_rfo_and_complete_audiences=True,
        fixed_criteria_and_recipients_current_adoption_and_service=True,
        actual_exposition_separate_from_creed_truth_and_personal_belief=True)


@lru_cache(None)
def quote_domain_checks():
    doc = deepcopy(catalog().document); doc['statements'] = []
    doc = parse(format_graph(doc, 'compact') + 'q[e[r b[p r35v]][r b[p r35v]]].')
    assert evaluate(doc, base(doc), DOMAIN, SCENES, True) == [True]
    try: parse(format_graph(catalog().document, 'compact') + 'q[e[r[p r35v]][r[p r35v]]].')
    except ValueError as error: rejected_rank = str(error)
    else: raise AssertionError('Rank zero accepted evaluation of rank zero descriptions')
    doc = fixture('r35v')
    try: evaluate(doc, model(doc), DOMAIN, SCENES, True)
    except ValueError as error:
        assert 'Cannot finitely quantify the description domain' in str(error), str(error); rejected_domain = str(error)
    else: raise AssertionError('All message descriptions finitely enumerated')
    return dict(rank_one_quote_without_execution=True, insufficient_rank_rejected=rejected_rank,
        full_message_domain_refused=rejected_domain, providers_receive_engine_created_closed_codes=True)


@lru_cache(None)
def unknown_checks():
    rows = []
    for target, name in (('r35r', 'zchoosebelief'), ('r35r', 'h246g'), ('r35s', 'zchoosestandard'),
        ('r35s', 'h246i'), ('r35u', 'h246k'), ('r35u', 'h246l'), ('r35u', 'zjudge'), ('r35u', 'zconditions')):
        doc = fixture(target); v = model(doc); v[name] = unknown
        try: evaluate(doc, v, DOMAIN, SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error), str(error)
        else: raise AssertionError(name)
        rows.append(name)
    return dict(unknown_inputs_refused=rows)


@lru_cache(None)
def structure_checks():
    new = catalog(); old = {n: e for p in parents() for n, e in p.entries.items()}
    assert not new.document['statements']
    for n, e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration'] == old[n]['declaration'] and e['meaning_ja'] == old[n]['meaning_ja'], n
    for path in PRIOR: validate_hashes(ROOT, read(path)['source_sha256'])
    validate_hashes(ROOT, {s['raw_archive']: s['raw_sha256'] for s in read(EVIDENCE)['sources']})
    for path, body in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for notation in ('compact', 'full'):
        text = format_graph(new.document, notation); assert parse(text) == parse(transcribe(text, alphabet='v2')) == new.document
    return dict(new_definitions=len(MEANINGS), new_primitives=len(PRIMITIVES), inherited_meanings_preserved=True,
        archived_lexical_sources_verified=True, roundtrips=True, active_manuscript_unchanged=True, new_semantic_reviews=0)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)


def build_report():
    results = {}
    for name, fn in [('profession', profession_checks), ('standard', standard_checks), ('teaching', teaching_checks),
        ('quotation_domain', quote_domain_checks), ('unknown', unknown_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    paths = set(build()) | set().union(*(set(p.source_sha256) for p in parents())) | {DOC, *PRIOR, EVIDENCE,
        'scripts/compose_confessional_teaching.py', 'scripts/check_confessional_teaching.py', 'tests/test_confessional_teaching.py',
        'scripts/compose_prescribed_teaching.py', 'scripts/check_clerical_audiences.py',
        'scripts/compose_grounded_step.py', 'scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='same_confession_adopted_standard_and_expository_teaching', document=LIBRARY, **results,
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
