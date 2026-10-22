"""Check distinct civic ranges, exact content bindings and non-executing presentation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_civic_participation_discourse import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,CRITICS,PETITION,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized

REPORT='reports/civic-participation-discourse-v1.json'
DOC='docs/civic-participation-discourse-v1.md'
READING='data/civic-participation-discourse-reading-v1.json'
PRIORS=('reports/institutional-criticism-v1.json','reports/joint-petition-v1.json','reports/protective-petition-v1.json','reports/appointed-roles-v1.json')
SCENES=('reference','candidate','anchor','later','outside','context')
NODES=('focus','public','written','aside','proposalnode','author')
OBJECTS=tuple(dict.fromkeys((*CRITICS,*PETITION,*NODES)))
EXTRA=''.join('r z'+n+'[] a.' for n in OBJECTS)+''.join('r z'+n+'[] d.' for n in SCENES)
EXTRA+='r zfact[d] c.d zwhole[] e[b point[k zfact[v point]]].'
CONTEXT='k zreference[] k zcandidate[] k zanchor[]'
CSEQ='l[a]['+' '.join('k z'+n+'[]' for n in CRITICS)+']'
PSEQ='l[a]['+' '.join('k z'+n+'[]' for n in PETITION)+']'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(roots,query,boundaries=()):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries and d['kind']=='definition':d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    return parse(format_graph(doc,'compact')+EXTRA+query)

def run(doc,v,domain=('alpha','beta')):return evaluate(doc,v,domain,SCENES,True)
def query(root,seq=CSEQ):return 'q[t[k '+root+'['+seq+' '+CONTEXT+']][k zlater[]]].'
def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda:'alpha' for n in OBJECTS})
    v.update({'z'+n:lambda n=n:n for n in SCENES})
    return v

def focus_model(doc,variant='baseline'):
    v=base(doc);v['zperson']=lambda:'beta'
    exact=tuple('beta' if n=='person' else 'alpha' for n in CRITICS)+('reference','candidate','anchor')
    v['r5e5']=lambda *a:a==exact and variant!='no_candidate'
    v['r5e6']=lambda *a:a==exact and variant!='no_permission'
    v['sp']=lambda p,t:(p,t)==('alpha' if variant=='other_cleric' else 'beta','later' if variant=='other_clerical_time' else 'anchor') and variant!='not_cleric'
    v['h26cs']=lambda g,c,r:(g,c,r)==('alpha','alpha','reference')
    v['h26cu']=lambda p,c,r,h,t:p in ('alpha','beta') and(c,r,h,t)==('alpha','reference','candidate','anchor')
    v['aa']=lambda p:p in ('alpha','beta')
    v['r5e7']=lambda p,c,g,r,h,t:(c,g,r,h,t)==('alpha','alpha','reference','candidate','anchor') and p in ('alpha','beta') and variant!='no_permission' and not(variant=='only_cleric_free' and p=='alpha')
    return v

@lru_cache(None)
def focus_checks():
    roots=('r5gy','r5gz','r5g2','r5g5')
    d=fixture(roots,''.join(query(n) for n in roots),('r5e5','r5e6','sp','r5e7'));rows={}
    for variant,expected in (
        ('baseline',[True,True,True,True]),('not_cleric',[True,False,True,True]),
        ('other_cleric',[True,False,True,True]),('other_clerical_time',[True,False,True,True]),
        ('only_cleric_free',[True,True,True,False]),('no_permission',[True,True,False,False]),
        ('no_candidate',[False,False,True,True])):
        actual=run(d,focus_model(d,variant));assert actual==expected,(variant,actual);rows[variant]=actual
    rejected=[]
    for name in ('r5e5','r5e6','sp','r5e7','h26cu'):
        v=focus_model(d);v[name]=unknown
        try:run(d,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(name)
        rejected.append(name)
    return dict(candidate_focus_individual_and_all_citizen_freedom=rows,native_all_citizen_quantification=True,
        focus_does_not_narrow_universal_freedom=True,
        boundaries=['r5e5/r5e6/r5e7; native criticism evidence preserved','sp; native appointed-role evidence preserved'],unknown_rejected=rejected)

@lru_cache(None)
def binding_checks():
    rows={}
    for root,target,names in (('r5gy','r5e5',CRITICS),('r5g2','r5e6',CRITICS),('r5g5','r5fa',CRITICS),('r5hb','r5gk',PETITION)):
        seq=CSEQ if names==CRITICS else PSEQ
        d=fixture((root,),query(root,seq),(target,));positions=[]
        for i in range(len(names)):
            vals=tuple('beta' if k==i else 'alpha' for k in range(len(names)));v=base(d)
            v.update({'z'+n:lambda value=value:value for n,value in zip(names,vals)})
            wanted=(*vals[:2],'reference','candidate','anchor') if root=='r5g5' else (*vals,'reference','candidate','anchor')
            v[target]=lambda *a,wanted=wanted:a==wanted
            assert run(d,v)==[True],(root,i)
            if root!='r5g5' or i<2:
                v['z'+names[i]]=lambda:'alpha';assert run(d,v)==[False],(root,i)
            positions.append(i)
        for length in (len(names)-1,len(names)+1):
            wrong_names=names[:length] if length<len(names) else (*names,names[0])
            seq='l[a]['+' '.join('k z'+n+'[]' for n in wrong_names)+']'
            wrong=fixture((root,),query(root,seq),(target,));v=base(wrong);v[target]=lambda *a:True
            assert run(wrong,v)==[False]
        rows[root]=positions
    return dict(exact_nine_or_four_targets=rows,wrong_lengths_rejected=True,
        boundaries=['r5e5','r5e6','r5fa','r5gk; native constructions checked separately'])

@lru_cache(None)
def explanation_checks():
    roots=('r5g3','r5g4');boundaries=('r2zi','cc','r3z','h243y','h243z')
    d=fixture(roots,''.join(query(n) for n in roots),boundaries);rows={}
    positions={
      'r2zi':('person','making','scholar'),'cc':('making','audience'),
      'r3z':('person','presenting','scholar','notes','audience'),
      'h243y':('person','making','notes'),'h243z':('presenting','notes','audience')}
    for name,used in positions.items():
        for slot in used:
            v=base(d);v['z'+slot]=lambda:'beta'
            expected={n:tuple('beta' if s==slot else 'alpha' for s in fields)+('reference',) for n,fields in positions.items()}
            v.update({n:lambda *a,wanted=wanted:a==wanted for n,wanted in expected.items()})
            assert run(d,v)==[True,True]
            old=v[name]
            def wrong(*a,old=old,name=name,slot=slot):
                a=list(a);a[positions[name].index(slot)]='alpha';return old(*a)
            v[name]=wrong;actual=run(d,v)
            wanted=[name not in ('r2zi','cc'),name in ('r2zi','cc')]
            assert actual==wanted,(name,slot,actual);rows[name+'_'+slot]=actual
    return dict(same_person_activities_notes_and_audience=rows,
        public_and_written_facets_are_distinct=True,
        boundaries=list(boundaries),native_components='institutional-criticism report preserves native r5e5 including these exact components')

def group_model(doc,variant='partial'):
    v=base(doc);v['zrecipient']=lambda:'beta';v['zpolicy']=lambda:'gamma'
    members=('alpha','beta','gamma') if variant in ('full','outsider_member') else ('alpha',) if variant=='single' else () if variant=='empty' else ('alpha','beta')
    citizens=('alpha','beta') if variant=='outsider_member' else ('alpha','beta','gamma')
    v['h26db']=lambda g,p,r,h,t:(g,r,h,t)==('alpha','reference','candidate','anchor') and p in members
    v['h26cu']=lambda p,c,r,h,t:(c,r,h,t)==('alpha','reference','candidate','anchor') and p in citizens
    v['aa']=lambda p:p in ('alpha','beta','gamma') and not(variant=='nonhuman' and p=='beta')
    v['r5gk']=lambda *a:variant in ('partial','full') and a==('alpha','alpha','beta','gamma','reference','candidate','anchor')
    if variant=='other_time_exclusion':
        v['h26db']=lambda g,p,r,h,t:(g,r,h)==('alpha','reference','candidate') and p in (('alpha','beta','gamma') if t=='anchor' else ('alpha','beta'))
    return v

@lru_cache(None)
def participation_checks():
    roots=('r5g6','r5g7','r5ha','r5hb');d=fixture(roots,''.join(query(n,PSEQ) for n in roots),('r5gk',));rows={}
    for variant,expected in (
        ('partial',[True,True,False,True]),('full',[True,False,True,True]),
        ('unavailable',[True,True,False,False]),('single',[False,False,False,False]),
        ('empty',[False,False,False,False]),('outsider_member',[False,False,False,False]),
        ('nonhuman',[False,False,False,False]),('other_time_exclusion',[True,False,True,False])):
        actual=run(d,group_model(d,variant),('alpha','beta','gamma'));assert actual==expected,(variant,actual);rows[variant]=actual
    rejected=[]
    for name in ('h26db','h26cu','aa','r5gk'):
        v=group_model(d);v[name]=unknown
        try:run(d,v,('alpha','beta','gamma'))
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(name)
        rejected.append(name)
    return dict(native_plural_membership_full_and_partial_ranges=rows,
        partial_membership_neither_required_nor_sufficient_for_proposal=True,
        same_anchor_membership=True,boundary='r5gk; native joint proposal evidence preserved',unknown_rejected=rejected)

@lru_cache(None)
def discourse_checks():
    q='q[k r5hc[k zfocus[] k zpublic[] k zwritten[] k zauthor[] r d[k zwhole[]] k zcontext[]]].'
    q+='q[k r5hd[k zaside[] k zproposalnode[] k zauthor[] r d[k zwhole[]] k zcontext[]]].'
    d=fixture(('r5hc','r5hd'),q);family=lambda n:(n,1);whole=('zwhole',3)
    expected={
      'h26d5':('focus','author',whole,family('r5g5'),family('r5gy'),family('r5gz'),family('r5g2'),'context'),
      'h26d6':('author','public','written',whole,family('r5gy'),family('r5g3'),family('r5g4'),'context'),
      'uf':('author','public','written','context'),'ue':('public','written','context'),
      'h26d7':('aside','author',whole,family('r5g6'),family('r5hb'),family('r5g7'),'context'),
      'h234k':('aside','author','proposalnode','context')}
    rows={}
    for variant in ('baseline',*expected,'wrong_author','wrong_context','different_whole','only_clerical_scope','other_public_facet','all_instead_of_not_all','reverse_explanation','merged_criticism_nodes','merged_aside'):
        v=base(d);v.update({'z'+n:lambda n=n:n for n in NODES});wanted=deepcopy(expected)
        if variant=='wrong_author':v['zauthor']=lambda:'focus'
        if variant=='wrong_context':v['zcontext']=lambda:'reference'
        changes={'different_whole':('h26d5',2,('r5gi',3)),
                 'only_clerical_scope':('h26d5',3,family('r5gz')),
                 'other_public_facet':('h26d6',5,family('r5g4')),
                 'all_instead_of_not_all':('h26d7',5,family('r5ha'))}
        if variant in changes:
            name,index,value=changes[variant];row=list(wanted[name]);row[index]=value;wanted[name]=tuple(row)
        if variant=='reverse_explanation':wanted['uf']=('author','written','public','context')
        v.update({n:lambda *a,n=n,row=row:n!=variant and normalized(a)==row for n,row in wanted.items()})
        if variant.startswith('merged_'):
            for n in expected:v[n]=lambda *a:True
            v['zwritten' if variant=='merged_criticism_nodes' else 'zproposalnode']=lambda:'public' if variant=='merged_criticism_nodes' else 'aside'
        actual=run(d,v,NODES)
        fail_civic=variant in ('h26d5','h26d6','uf','ue','different_whole','only_clerical_scope','other_public_facet','reverse_explanation','merged_criticism_nodes')
        fail_aside=variant in ('h26d7','h234k','all_instead_of_not_all','merged_aside')
        if variant in ('wrong_author','wrong_context'):fail_civic=fail_aside=True
        assert actual==[not fail_civic,not fail_aside],(variant,actual);rows[variant]=actual
        for n in ('zfact','h26cu','h26db','h7l','h7k'):assert v[n] is unknown
    for name in ('h26d5','h26d6','h26d7'):
        v=base(d);v.update({'z'+n:lambda n=n:n for n in NODES})
        v.update({n:lambda *a,row=row:normalized(a)==row for n,row in expected.items()});v[name]=unknown
        try:run(d,v,NODES)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(name)
    return dict(same_whole_author_families_explanation_focus_and_aside=rows,
        quoted_citizenship_permission_and_proposal_not_executed=True,unknown_rejected=True)

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';u=next(x for x in read(inv)['units'] if x['id']=='kant-1784:u0013');text=u['text'];parts=[]
    for fragment,names in (
        ('jedem der Bürger, vornehmlich dem Geistlichen',['r5g5','r5gy','r5gz','r5g2','r5hc']),
        ('öffentlich, d. i. durch Schriften',['r5g3','r5g4','r5hc']),
        ('durch Vereinigung ihrer Stimmen (wenn gleich nicht aller)',['r5g6','r5g7','r5ha','r5hb','r5hd'])):
        start=text.index(fragment,1437,2309);parts.append(dict(range=[start,start+len(fragment)],text=fragment,definitions=names))
    return dict(status='civic_participation_discourse_dependency',source_inventory=inv,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1437,2309],text=text[1437:2309]),
        parts=parts,adopted_readings=LIMITS,
        remaining=['whole-sentence quantification','protective purpose and hypothetical reformers','throne metonymy and Nun wohl gleichsam','same whole-content attribution and holistic review'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)

@lru_cache(None)
def structure_checks():
    sources=parents();new=catalog();old={n:e for s in sources for n,e in s.entries.items()}
    for n,e in new.entries.items():
        if n not in set(PRIMITIVES)|set(MEANINGS):assert e['declaration']==old[n]['declaration'] and e['meaning_ja']==old[n]['meaning_ja'],n
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record() and not new.document['statements'] and len(sources[0].document['statements'])==102
    proposed={d['name'] for d in closure(new.document,['r5hb'])}
    assert not proposed&{'r5g7','r5ha','r5gz','sp'}
    focused={d['name'] for d in closure(new.document,['r5gz'])}
    assert 'sp' in focused and not focused&{'r35t','r35q','r35o','r5e6'}
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        focus_and_concession_not_hidden_world_preconditions=True,preserved_manuscript_statements=102)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('focus',focus_checks),('bindings',binding_checks),('explanation',explanation_checks),('participation',participation_checks),('discourse',discourse_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,reading_record()['source_inventory'],
        'scripts/compose_civic_participation_discourse.py','scripts/check_civic_participation_discourse.py','tests/test_civic_participation_discourse.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py','scripts/compose_institutional_criticism.py'}
    return dict(status='civic_participation_discourse_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
