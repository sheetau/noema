"""Check highest offices, estate representation, solemn forms and confirmation."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_public_confirmation import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.fetch_public_confirmation_evidence import RECORD as EVIDENCE,validate

REPORT='reports/public-confirmation-v1.json'
DOC='docs/public-confirmation-v1.md'
READING='data/public-confirmation-reading-v1.json'
PRIORS=('reports/covenant-question-v1.json','reports/church-councils-v1.json','reports/delegated-associations-v1.json')
DOMAIN=('top','low','peer','actor','body','estate','empire','community','instrument','contract','person','role','activity','issue')
SCENES=('reference','candidate','other')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r zt'+n+'[] d.' for n in SCENES)+'r zkind[a d] c.'

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
def office_checks():
    doc=fixture(('r5am',),'q[k r5am[k ztop[] k zbody[] k ztcandidate[]]].');rows={}
    roles=('top','low','peer')
    for variant in ('baseline','incomparable_peer','cycle','nontransitive','missing_top','other_organization','other_point','singleton'):
        v=base(doc);scope=roles if variant!='singleton' else ('top',)
        if variant=='missing_top':scope=('low','peer')
        v['h256p']=lambda role,org,point:role in scope and (org,point)==('body','candidate')
        edges={('top','low'),('top','peer'),('peer','low')}
        if variant=='incomparable_peer':edges={('top','low'),('peer','low')}
        if variant=='cycle':edges.add(('low','top'))
        if variant=='nontransitive':edges.remove(('top','low'))
        v['h256q']=lambda a,b,org,p:(a,b) in edges and (org,p)==('estate' if variant=='other_organization' else 'body','other' if variant=='other_point' else 'candidate')
        result=run(doc,v,('top','low','peer','body'));assert result==[variant in ('baseline','singleton')],(variant,result);rows[variant]=result[0]
    d=fixture(('r5an',),'q[k r5an[k zactor[] k zcommunity[] k ztcandidate[]]].',('r5am',));holders={}
    for variant in ('baseline','not_highest','other_holder','other_office','other_organization','private_company','other_community','other_point'):
        v=base(d);v['r5am']=lambda office,org,p:variant!='not_highest' and (office,org,p)==('top','body','candidate')
        expected=['actor','top','body','candidate']
        changes={'other_holder':(0,'person'),'other_office':(1,'low'),'other_organization':(2,'estate'),'other_point':(3,'other')}
        if variant in changes:i,x=changes[variant];expected[i]=x
        v['h256r']=lambda *args:args==tuple(expected)
        v['h256s']=lambda org,c,p:variant!='private_company' and (org,c,p)==('body','empire' if variant=='other_community' else 'community','candidate')
        result=run(d,v);assert result==[variant=='baseline'],(variant,result);holders[variant]=result[0]
    return dict(native_order=rows,holder_and_public_jurisdiction=holders,boundary='r5am only in holder quantification; native order checked separately')

@lru_cache(None)
def representation_checks():
    doc=fixture(('r5ao',),'q[k r5ao[k zperson[] k zestate[] k zbody[] k ztcandidate[]]].');rows={}
    for variant in ('direct','delegated','no_human','no_mandate','wrong_assembly','no_role','no_appointment','no_service'):
        v=base(doc);v['aa']=lambda p:variant!='no_human' and p=='person'
        v['h256u']=lambda *args:variant=='direct' and args==('person','estate','body','candidate')
        v['h254f']=lambda *args:variant not in ('no_mandate','direct') and args==('estate','person','role','empire' if variant=='wrong_assembly' else 'body','candidate')
        v['hzwn']=lambda *args:variant!='no_role' and args==('person','role','candidate')
        v['hzxf']=lambda *args:variant!='no_appointment' and args==('person','role','estate','candidate')
        v['h246k']=lambda *args:variant!='no_service' and args==('person','estate','role','candidate')
        result=run(doc,v);assert result==[variant in ('direct','delegated')],(variant,result);rows[variant]=result[0]
    d=fixture(('r5ap',),'q[k r5ap[k zbody[] k zempire[] k ztcandidate[]]].',('r5ao',));coverage={}
    for variant in ('baseline','empty_estates','unrepresented_estate','unqualified_member','other_empire','private_assembly','other_point'):
        v=base(d);estates=() if variant=='empty_estates' else ('estate','peer') if variant=='unrepresented_estate' else ('estate',)
        v['h254g']=lambda body,e,p:body=='body' and e in estates and p=='candidate'
        v['h246c']=lambda body,person,p:body=='body' and person in (('person','actor') if variant=='unqualified_member' else ('person',)) and p=='candidate'
        v['h256v']=lambda *a:variant!='private_assembly' and a==('body','empire','candidate')
        v['h256t']=lambda e,empire,p:e in ('estate','peer') and (empire,p)==('community' if variant=='other_empire' else 'empire','candidate')
        v['r5ao']=lambda *a:a==('person','estate','body','other' if variant=='other_point' else 'candidate')
        result=run(d,v);assert result==[variant=='baseline'],(variant,result);coverage[variant]=result[0]
    return dict(native_direct_and_delegated_roles=rows,native_two_sided_representation=coverage,boundary='r5ao in assembly coverage; native representative checked separately')

@lru_cache(None)
def practice_checks():
    doc=fixture(('r5aq',),'q[t[k r5aq[k zperson[] k zbody[] k zactivity[] k zissue[] k zempire[]]][k ztcandidate[]]].');rows={}
    expected=dict(h246c=('body','person','candidate'),dg=('activity','candidate'),f3=('person','activity','candidate'),
        h254i=('activity','body','candidate'),h254h=('activity','issue','candidate'),h254j=('body','issue','candidate'),
        h256v=('body','empire','candidate'),h256w=('issue','empire','candidate'))
    for missing in (None,*expected):
        v=base(doc);v.update({n:lambda *a,n=n,args=args:n!=missing and a==args for n,args in expected.items()})
        result=run(doc,v);assert result==[missing is None];rows[str(missing)]=result[0]
    d=fixture(('r5ar',),'q[t[k r5ar[k zperson[] k zbody[]]][k ztcandidate[]]].',('r5aq',));v=base(d)
    v['r5aq']=lambda *a:Content(SCENES,tuple(a==('person','body','activity','issue','empire') and s=='candidate' for s in SCENES))
    assert run(d,v)==[True]
    d=fixture(('r5as',),'q[k r5as[k zbody[] k ztcandidate[]]].',('r5ap',));quoted={}
    for variant in ('baseline','no_estate_body','no_practice','wrong_code','wrong_body','wrong_point'):
        v=base(d);v['r5ap']=lambda *a:variant!='no_estate_body' and a==('body','empire','candidate')
        v['h246h']=lambda body,code,p:variant!='no_practice' and code.rank==0 and (body,symbol(code),p)==(
            'estate' if variant=='wrong_body' else 'body','r46e' if variant=='wrong_code' else 'r5ar','other' if variant=='wrong_point' else 'candidate')
        result=run(d,v);assert result==[variant=='baseline'];quoted[variant]=result[0]
        assert v['dg'] is unknown
    return dict(native_single_activity=rows,practice_adapter_native_quantifiers=True,unexecuted_practice=quoted,boundaries=['r5aq for practice adapter','r5ap for institutional practice'])

@lru_cache(None)
def solemnity_checks():
    doc=fixture(('r5at',),'q[k r5at[k ztop[] k ztreference[]]].');rows={}
    forms=('top','peer','low')
    for variant in ('baseline','tied_highest','incomparable','cycle','empty','outside','not_solemn','moving_reference'):
        v=base(doc);scope=() if variant=='empty' else ('peer','low') if variant=='outside' else forms
        v['h256z']=lambda form,r:form in scope and r=='reference'
        v['h257c']=lambda form,r:variant!='not_solemn' and (form,r)==('top','reference')
        rank=dict(top=2,peer=2 if variant=='tied_highest' else 1,low=0)
        edges={(a,b) for a in forms for b in forms if rank[a]>=rank[b]}
        if variant=='incomparable':edges.discard(('top','peer'));edges.discard(('peer','top'))
        if variant=='cycle':edges.add(('low','top'))
        v['h257a']=lambda a,b,r:(a,b) in edges and r==('candidate' if variant=='moving_reference' else 'reference')
        result=run(doc,v,forms);assert result==[variant in ('baseline','tied_highest')],(variant,result);rows[variant]=result[0]
    d=fixture(('r5au',),'q[k r5au[k zinstrument[] k ztreference[] k ztcandidate[]]].',('r5at',));same={}
    for variant in ('baseline','other_instrument','other_form','other_point','moving_reference'):
        v=base(d);v['r5at']=lambda f,r:(f,r)==('top','candidate' if variant=='moving_reference' else 'reference')
        v['h257b']=lambda *a:a==('contract' if variant=='other_instrument' else 'instrument','low' if variant=='other_form' else 'top','other' if variant=='other_point' else 'candidate')
        result=run(d,v);assert result==[variant=='baseline'];same[variant]=result[0]
    return dict(native_weak_greatest=rows,same_instrument_fixed_comparison= same,boundary='r5at only for instrument adapter')

@lru_cache(None)
def confirmation_checks():
    doc=fixture(('r5ay',),'q[t[k r5ay[k zcontract[] k zcommunity[] k ztreference[] p zkind]][k ztcandidate[]]].',('r5an','r5as','r5au'));cases=0
    def model(flags,variant='baseline'):
        v=base(doc)
        v['r5an']=lambda *a:a==('actor','empire' if variant=='other_community' else 'community','candidate')
        v['r5as']=lambda *a:a==('body','candidate')
        v['r5au']=lambda *a:a==('instrument','candidate' if variant=='moving_reference' else 'reference','candidate')
        v['zkind']=lambda *a:variant!='wrong_kind' and a==('instrument','candidate')
        v['h256x']=lambda a,c,p: c==('instrument' if variant=='wrong_contract' else 'contract') and p==('other' if variant=='other_point' else 'candidate') and ((flags[0] and a=='actor') or (flags[1] and a=='body'))
        v['h256y']=lambda i,c,p:flags[2] and (i,c,p)==('body' if variant=='personified_document' else 'instrument','instrument' if variant=='wrong_contract' else 'contract','other' if variant=='other_point' else 'candidate')
        return v
    for flags in product((False,True),repeat=3):
        result=run(doc,model(flags));assert result==[any(flags)];cases+=1
    contrasts={}
    for variant,flags in [('other_community',(True,False,False)),('moving_reference',(False,False,True)),('wrong_kind',(False,False,True)),
        ('wrong_contract',(True,True,True)),('other_point',(True,True,True)),('personified_document',(False,False,True))]:
        result=run(doc,model(flags,variant));assert result==[False],(variant,result);contrasts[variant]=result[0]
    for name in ('h256x','h256y','zkind'):
        v=model((True,True,True));v[name]=unknown
        try:run(doc,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(name)
    return dict(native_three_branch_cases=cases,same_contract_and_kind=contrasts,unknown_rejected=True,
        boundaries=['r5an','r5as','r5au'],normative_effect_not_inferred=True,peace_kind_still_explicit_parameter=True)

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';unit=next(u for u in read(inv)['units'] if u['id']=='kant-1784:u0013')
    return dict(status='public_confirming_agents_and_solemn_instruments_dependency',source_inventory=inv,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[444,712],text=unit['text'][444:712]),
        primary_page=read('data/covenant-question-reading-v1.json')['original_page'],evidence=EVIDENCE,adopted_readings=LIMITS,
        remaining=['和平締結の交戦主体・和平の相互引受け・同じ合意の形成という分類をr5ax/r5ayへ供給する',
            '同種契約の仮定形成と無効性の内容を結ぶ','列挙・最上級・schlechterdings・sollte auchの談話提示と全文への著者帰属','一文の通読による意味判断'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)

@lru_cache(None)
def structure_checks():
    new,old=catalog(),parent()
    for n,e in new.entries.items():
        if n not in set(PRIMITIVES)|set(MEANINGS):
            assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    validate(read(EVIDENCE));assert read(READING)==reading_record()
    p=read(READING)['primary_page'];assert digest((ROOT/p['path']).read_bytes())==p['sha256']
    assert not new.document['statements'] and len(old.document['statements'])==98
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_manuscript_statements=98)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('offices',office_checks),('representation',representation_checks),('practice',practice_checks),('solemnity',solemnity_checks),('confirmation',confirmation_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,EVIDENCE,*PRIORS,read(READING)['source_inventory'],read(READING)['primary_page']['path'],
        'scripts/compose_public_confirmation.py','scripts/check_public_confirmation.py','scripts/fetch_public_confirmation_evidence.py','tests/test_public_confirmation.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_spiritual_guardians.py'}
    paths|={r['path'] for r in read(EVIDENCE)['sources']}
    return dict(status='public_confirming_agents_and_solemn_instruments_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
