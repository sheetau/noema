"""Check independent state and attitude scopes without equating stance with mood."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts.compose_scoped_attitude import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,MEANINGS,parent,build,closure
from scripts.check_motive_causes import evaluate,unknown,symbol
from scripts.check_designation_order import substantive

REPORT='reports/scoped-attitude-v1.json'
AUDIT='data/scoped-attitude-reading-v1.json'
INDEX='data/semantic-review-index-v42.json'
DOC='docs/scoped-attitude-v1.md'
SCENES=('early','middle','late')
DOMAIN=('person','other')


@lru_cache(None)
def candidate():
    catalog=load_catalog(ROOT,BASIS)
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8'))
    doc=parse(format_graph(doc,'compact')+'''
r jperson[] a.r jreference[] d.r jstate[a d] c.r jother[a d] c.r joccasions[d] c.
d bf[person a] e[b scene[k jstate[v person v scene]]].
d jproperty[person a] e[b scene[k jother[v person v scene]]].
''')
    # This fixture preserves the stored ie body, but makes its bf property
    # explicit and abstract. It does not re-run the complete ability analysis.
    doc['declarations'] += [deepcopy(catalog.entries[n]['declaration']) for n in ('ia','ib','ic','id','ie')]
    text=format_graph(doc,'compact')
    for name in ('bf','jproperty'):
        text+='q[k rqxf[k jperson[] r[p '+name+'] i[scene d][k ia[k jperson[] k jreference[] v scene]] '+\
            'i[scene d][k ib[k jperson[] k jreference[] v scene]] p joccasions '+\
            'i[first d second d][k ic[v first v second k jreference[]]] p id]].'
    text+='q[t[k ie[k jperson[]]][k jreference[]]].'
    return parse(text)


def values(states=(True,True,True),attitudes=(True,True,True),variant='baseline'):
    scope=set(SCENES);occasions=set(SCENES)
    if variant=='sparse':occasions={'early','late'}
    if variant=='empty_occasions':occasions=set()
    if variant=='empty_extent':scope=set()
    if variant=='outside_occasion':scope={'early','middle'}
    if variant=='hole':scope={'early','late'}
    if variant=='truncated':scope={'early','middle'};occasions=set(scope)
    def accepts(person,description,scene):
        return person==('other' if variant=='other_person' else 'person') and symbol(description)==(
            'jproperty' if variant=='other_property' else 'bf') and attitudes[SCENES.index(scene)]
    return dict(jperson=lambda:'person',jreference=lambda:'late',
        jstate=lambda person,scene:person=='person' and states[SCENES.index(scene)],
        jother=lambda person,scene:person=='person' and states[SCENES.index(scene)],
        joccasions=lambda scene:scene in occasions,
        ia=lambda person,context,scene:person=='person' and context=='late' and not (variant=='outside_history' and scene=='early'),
        ib=lambda person,context,scene:person=='person' and context==('middle' if variant=='other_context' else 'late') and scene in scope,
        ic=lambda first,second,context:context=='late' and (SCENES.index(first)<SCENES.index(second) or
            variant=='cycle' and (first,second)==('late','early')),
        id=accepts)


def scope_checks():
    doc=candidate();rows=[]
    for bits in product((False,True),repeat=6):
        actual=evaluate(doc,values(bits[:3],bits[3:]),DOMAIN,SCENES)
        assert actual==[all(bits),False,all(bits)],(bits,actual)
        rows.append(dict(states=list(bits[:3]),attitudes=list(bits[3:]),values=actual))
    expected=dict(baseline=[True,False,True],sparse=[True,False,True],empty_occasions=[False,False,True],
        empty_extent=[False,False,False],outside_occasion=[False,False,True],hole=[False,False,False],
        other_person=[False,False,False],other_property=[False,True,False],other_context=[False,False,False],
        outside_history=[False,False,False],cycle=[False,False,False])
    contrasts={}
    for variant,result in expected.items():
        contrasts[variant]=evaluate(doc,values(variant=variant),DOMAIN,SCENES)
        assert contrasts[variant]==result,(variant,contrasts[variant])
    selective=evaluate(doc,values(attitudes=(True,False,True),variant='sparse'),DOMAIN,SCENES)
    assert selective==[True,False,False]
    gap=evaluate(doc,values(states=(True,False,True),variant='sparse'),DOMAIN,SCENES)
    assert gap==[False,False,False]
    # A finite interval checker cannot certify that its input spans a whole
    # biological life. Expose that limit instead of giving false assurance.
    full=evaluate(doc,values(states=(True,True,False)),DOMAIN,SCENES)
    truncated=evaluate(doc,values(states=(True,True,False),variant='truncated'),DOMAIN,SCENES)
    assert full==[False,False,False] and truncated==[True,False,True]
    for name in ('ia','ib','ic','id','jstate','joccasions'):
        v=values();v[name]=unknown
        try:evaluate(doc,v,DOMAIN,SCENES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(combinations=rows,contrasts=contrasts,missing_attitude_between_opportunities=selective,
        missing_state_between_opportunities=gap,full_range=full,truncated_observation=truncated,
        finite_interval_check_does_not_certify_whole_lifetime=True,
        unknown_inputs_refused=6,ordinary_evaluation=True,same_description_drives_state_and_attitude=True,
        actual_ie_body_executed_with_explicit_abstract_bf=True,complete_ability_semantics_reexecuted=False)


def attribution_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    for variant in ('baseline','other_author','other_node','other_scene','other_target','other_depiction','reverse_order'):
        v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        author='other' if variant=='other_author' else 'author'
        context='other' if variant=='other_scene' else 'text'
        def claim(node,who,content,scene):
            return (node,who,symbol(content),scene)==('other' if variant=='other_node' else 'cause',author,'mx',context)
        def framing(node,who,target,depiction,scene,binary=False):
            names=('h2a','h2b') if binary else ('kf','qg')
            expected_target='ie' if variant=='other_target' else names[0]
            expected_depiction='qf' if variant=='other_depiction' else names[1]
            return (node,who,symbol(target),symbol(depiction),scene)==(
                'other' if variant=='other_node' else 'frame' if binary else 'cause',author,expected_target,expected_depiction,context)
        v.update(mw=lambda:'cause',h2d=lambda:'frame',wa=lambda:'author',wh=lambda:'text',wg=lambda:'opening',uc=claim,
            qa=framing,rbt=lambda *args:framing(*args,binary=True),
            ue=lambda a,b,s:(a,b,s)==(('cause','opening','text') if variant=='reverse_order' else ('opening','cause','text')))
        rows[variant]=evaluate(doc,v,('cause','frame','author','opening','other'),('text',))
        expected=[variant in ('baseline','other_target','other_depiction'),variant in ('baseline','reverse_order'),variant in ('baseline','reverse_order')]
        assert rows[variant]==expected,(variant,rows[variant])
    return dict(contrasts=rows,all_state_attitude_and_life_inputs_unknown=True,ordinary_evaluation=True)


def structure():
    old,new=parent(),load_catalog(ROOT,BASIS)
    assert old.document['statements']==new.document['statements'] and len(new.document['statements'])==42
    assert set(new.entries)-set(old.entries)=={'rqxf'}
    assert all(old.entries[n]['declaration']==new.entries[n]['declaration'] for n in old.entries)
    changed=[n for n in old.entries if substantive(old.entries[n])!=substantive(new.entries[n])]
    assert set(changed)=={'ib','id','ie'}
    affected=[i for i,s in enumerate(new.document['statements']) if set(changed)&{d['name'] for d in closure(new.document,_references(s))}]
    assert affected==[2,3,11],affected
    index=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[r['index'] for r in review['selection']['statements']]
        before,after=selection_binding(old,indices),selection_binding(new,indices)
        assert before==review['selection'] and before['statements']==after['statements'] and before['dependencies']==after['dependencies']
        assert not set(indices)&set(affected)
        assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in before['dependencies'])
    for name,body in build().items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    for name in (FULL,CORE,LIBRARY):
        d=parse((ROOT/name).read_text(encoding='utf-8'))
        for style in ('compact','full'):
            text=format_graph(d,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    return dict(preserved_statements=42,changed_definitions=[],changed_meanings=sorted(changed),affected_statements=affected,
        new_definitions=1,new_primitive_relations=0,preserved_review_meanings=11,roundtrips=True)


def audit():
    inv='artifacts/written-units-v1/kant-1784.json'
    unit=next(u for u in json.loads((ROOT/inv).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    phrase='gerne Zeitlebens unmündig bleiben';start=unit['text'].index(phrase)
    return dict(status='standing_attitude_reading_and_independent_scopes_not_whole_sentence_review',reviewer='assistant_review',
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(phrase)],text=phrase),
        consulted='https://korpora.org/Kant/aa08/035.html',
        findings=['旧記録は全時点での態度を要求する一方、瞬間的な気分と保持された態度の区別を未確定にしていた。',
            '区間の整合性検査だけでは、途中で打ち切った観測範囲を実際の生涯全体と区別できない。'],
        decisions=['gerneを、未成熟な状態を好ましく受け入れる保持された態度として読む。全瞬間の快感や注意を要求する読みにはしない。',
            '生涯の範囲は文脈上の開始から生涯の終わりまでの全範囲と明記する。良い点だけを抜き出すこと、途中で打ち切ることを意味規約で認めない。',
            '原文用ieの本体は維持する。一般形では同じ性質の内容と記述を一体にし、状態範囲と態度機会を別引数にする。',
            '無反応だけから肯定的態度を推定せず、真に態度が反転した場合は全範囲での態度維持と区別する。'],
        remaining=['範囲や態度の実世界への適用には根拠が必要であり、有限実行では生涯や心理状態を証明しない。',
            '第一文の自然的成熟・ラテン語・割合・容易さと、第二段落全体の意味確認。'],
        whole_unit_semantically_verified=False,
        test_limit='現行ieの本体を、bfの性質に明示的な検査用解釈を与えた文書で実行する。能力判定全体や人口比率まで再実行したとはしない。',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (inv,PARENT,PARENT_BASIS,
            'docs/persistence-v1.md','docs/retained-attitudes-v1.md','docs/relative-past-v1.md')})


def build_report():
    results={}
    for name,fn in [('scopes',scope_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    reading=audit();assert json.loads((ROOT/AUDIT).read_text(encoding='utf-8'))==reading
    paths=set(build())|set(parent().source_sha256)|set(reading['source_sha256'])|{AUDIT,INDEX,DOC,
        'scripts/compose_scoped_attitude.py','scripts/check_scoped_attitude.py','tests/test_scoped_attitude.py',
        'scripts/check_motive_causes.py','scripts/check_designation_order.py','scripts/compose_falling_depiction.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py',
        'noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    source=reading['source']
    return dict(status='partial_standing_attitude_and_independent_scopes',document=FULL,**results,
        alignment=dict(unit=source['unit'],unit_sha256=source['unit_sha256'],range=source['range'],source=source['text'],
            definitions=['rqxf','ie','tc','td'],status='explicit_interpretive_annotation',full_semantic_equivalence=False),
        new_covered_characters=0,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(audit()));write_exact(ROOT/REPORT,encoded(build_report()))
    print('Persistence and attitude scopes checked',flush=True)


if __name__=='__main__':main()
