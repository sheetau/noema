"""Check candidate/actual separation and exact nonexecuted freedom targets."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_scholarly_own_voice import ROOT,LIBRARY,BASIS,NAMES,PRIMITIVES,MEANINGS,parent,build
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

REPORT='reports/scholarly-own-voice-v1.json'
DOC='docs/scholarly-own-voice-v1.md'
EVIDENCE='data/scholarly-own-voice-evidence-v1.json'
PRIORS=('reports/clerical-private-conclusion-v1.json',)
DOMAIN=(*NAMES,'listener','other','norm','record','medium')
SCENES=('reference','outcome')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+'r zref[] d.r zpoint[] d.'
EXTRA+='r zmeaning[a] e.d zmessage[subject a] f[j s[k zmeaning[v subject]]].d zalias[subject a] f[k zmessage[v subject]].'
SEQ='l[a]['+' '.join('k z'+n+'[]' for n in NAMES)+']'
ARGS=' '.join('k z'+n+'[]' for n in NAMES)+' r[p zmessage] k zref[]'
REASON='k zperson[] k zactivity[] k zscholar[] k zref[]'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(query=None):
    doc=deepcopy(catalog().document);doc['statements']=[]
    if query is None:
        query='q[k r44s['+ARGS+']].'+''.join('q[t[k '+n+'['+ARGS+']][k zpoint[]]].' for n in ('r44t','r44z'))
    return parse(format_graph(doc,'compact')+EXTRA+query)


def target(code):
    assert code.rank==1
    syntax=json.loads(code.syntax)
    if syntax['kind']=='function_ref':return syntax['symbol'],None
    assert syntax['kind']=='apply' and len(syntax['arguments'])==1
    function=syntax['function'];assert function['kind']=='lambda' and function['body']['kind']=='lambda'
    assert function['body']['body']['kind']=='call' and function['body']['body']['symbol']=='r44v'
    argument=syntax['arguments'][0]
    assert argument['kind']=='quote' and argument.get('rank',0)==0 and argument['body']['kind']=='function_ref'
    return 'r44v',argument['body']['symbol']


def model(doc,variant='baseline',bits=(True,False,True,False),focused=False):
    values={n:('one' if i%2==0 else 'two') if focused else n for i,n in enumerate(DOMAIN)}
    a=lambda n:values[n]
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:a(n) for n in DOMAIN});v.update(zref=lambda:'reference',zpoint=lambda:'outcome')
    seen={'norms':[],'execution':[],'voice':[]}
    def relation(name,wanted):
        def check(*actual):
            if name in ('cg','sc','hzwr','hzws','hzwt','dg','f3'):seen['execution'].append((name,actual))
            return variant!='missing_'+name and not (name=='hzwr' and variant=='missing_sd') and actual==wanted
        return check
    for n,wanted in {
        'aa':(a('person'),),'ca':(a('person'),a('activity'),'reference'),
        'cb':(a('person'),a('activity'),a('scholar'),'reference'),'cd':(a('scholar'),'reference'),
        'cc':(a('activity'),a('audience'),'reference'),'ce':(a('audience'),'reference'),
        'h242g':(a('activity'),a('writing'),a('audience'),'reference'),
        'cg':(a('person'),a('activity'),'outcome'),'sc':(a('writing'),'outcome'),
        'hzwr':(a('record'),a('writing'),'outcome'),'hzws':(a('record'),a('medium'),'outcome'),'hzwt':(a('record'),'outcome'),
        'dg':(a('activity'),'outcome'),'f3':(a('person'),a('activity'),'outcome'),
        'h6t':(a('audience'),a('listener'),'reference'),
    }.items():v[n]=relation(n,wanted)
    def voice(person,activity,principal,role,subject,message,point):
        row=(person,activity,principal,role,subject,symbol(message),message.rank,point);seen['voice'].append(row)
        expected=[a('person'),a('activity'),a('person'),a('scholar'),a('subject'),'zmessage',0,point]
        fields=('person','activity','principal','role','subject','message','rank')
        for i,n in enumerate(fields):
            if variant=='voice_'+n:expected[i]=1 if n=='rank' else 'other'
        return row==tuple(expected) and point in SCENES and not (
            variant=='no_candidate_voice' and point=='reference' or variant=='no_actual_voice' and point=='outcome')
    def conveys(activity,listener,subject,message,point):
        seen['execution'].append(('f2',(activity,listener,subject,symbol(message),point)))
        return variant!='missing_f2' and (activity,listener,subject,symbol(message),point)==(
            a('activity'),a('other') if variant=='outsider_only' else a('listener'),a('subject'),'zmessage','outcome')
    def source(person,scholar,ref):
        return a('norm') if variant!='other_source' and (person,scholar,ref)==(a('person'),a('scholar'),'reference') else a('other')
    def norm(permission):
        def check(source,person,role,code,bindings,ref,positive,point):
            name,message=target(code)
            row=(source,person,role,name,message,tuple(bindings.items),ref,positive,point)
            seen['norms'].append(('permission' if permission else 'demand',row))
            reason=name=='r44u';wanted_names=('person','activity') if reason else NAMES
            wanted=[a('norm'),a('person'),a('scholar'),'r44u' if reason else 'r44v',None if reason else 'zmessage',
                tuple(a(n) for n in wanted_names),'reference',permission,'outcome']
            fields=('source','person','role','target','message','bindings','reference','polarity','point')
            for i,n in enumerate(fields):
                if variant=='norm_'+n:wanted[i]=not permission if n=='polarity' else () if n=='bindings' else 'other'
            enabled=bits[(0 if reason else 2)+(0 if permission else 1)]
            return enabled and row==tuple(wanted)
        return check
    v.update(h253l=voice,f2=conveys,h247b=source,h245c=norm(True),h237z=norm(False))
    return v,seen


def run(doc,v,focused=False):return evaluate(doc,v,('one','two') if focused else DOMAIN,SCENES,True)


@lru_cache(None)
def candidate_checks():
    doc=fixture();rows={}
    failures=('aa','ca','cb','cd','cc','ce','h242g')
    for variant in ('baseline',*('missing_'+n for n in failures),'no_candidate_voice',
        *('voice_'+n for n in ('person','activity','principal','role','subject','message','rank'))):
        v,_=model(doc,variant);result=run(doc,v);assert result==([True]*3 if variant=='baseline' else [False]*3),(variant,result)
        rows[variant]=result
    for variant in (*('missing_'+n for n in ('cg','sc','sd','hzwr','hzws','hzwt','dg','f3','f2','h6t')),'no_actual_voice','outsider_only'):
        v,_=model(doc,variant);result=run(doc,v);assert result==[True,False,True],(variant,result);rows[variant]=result
    freedom=fixture('q[t[k r44z['+ARGS+']][k zpoint[]]].');v,seen=model(freedom)
    for n in ('cg','sc','hzwr','hzws','hzwt','dg','f3','f2','h6t','zmeaning'):v[n]=unknown
    assert run(freedom,v)==[True] and not seen['execution']
    for n in ('h253l','ce','h245c','h237z'):
        v,_=model(freedom);v[n]=unknown
        try:run(freedom,v)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(n)
    return dict(contrasts=rows,no_execution_or_truth_required_for_freedom=True,
        positive_self_attribution_required=True,one_public_recipient_suffices=True,unknown_rejected=True)


@lru_cache(None)
def norm_checks():
    doc=fixture('q[t[k r44x['+REASON+']][k zpoint[]]].'+''.join('q[t[k '+n+'['+ARGS+']][k zpoint[]]].' for n in ('r44y','r44z')))
    rows=[]
    for bits in product((False,True),repeat=4):
        v,seen=model(doc,bits=bits);result=run(doc,v);a=bits[0] and not bits[1];b=bits[2] and not bits[3]
        assert result==[a,b,a and b],(bits,result);rows.append([*bits,*result])
        assert {r[1][3] for r in seen['norms']}=={'r44u','r44v'} and not seen['execution']
    contrasts={}
    for variant in ('other_source',*('norm_'+n for n in ('source','person','role','target','message','bindings','reference','polarity','point'))):
        v,_=model(doc,variant);result=run(doc,v);assert result==[False]*3,(variant,result);contrasts[variant]=result
    alias=fixture('q[t[k r44y['+ARGS.replace('r[p zmessage]','r[p zalias]')+']][k zpoint[]]].')
    v,seen=model(alias);assert run(alias,v)==[False]
    assert any(r[1][4]=='zalias' for r in seen['norms'])
    return dict(two_separate_permission_prohibition_tables=rows,contrasts=contrasts,
        exact_code_message_bindings_reference_point_and_polarity=True,alias_not_substituted=True)


@lru_cache(None)
def target_checks():
    direct='t[k r44t['+ARGS+']][k zpoint[]]'
    adapted='t[k r44v[r[p zmessage] '+SEQ+' k zref[]]][k zpoint[]]'
    constructed='t[c[s[k r44w[r[p zmessage]]]]['+SEQ+' k zref[]]][k zpoint[]]'
    doc=fixture(''.join('q['+q+'].' for q in (direct,adapted,constructed)));rows={}
    for variant in ('baseline','missing_cg','missing_sd','no_candidate_voice','no_actual_voice','missing_f2'):
        v,_=model(doc,variant,focused=True);result=run(doc,v,True);assert result==[variant=='baseline']*3,(variant,result);rows[variant]=result
    # Six distinct argument positions, but two individual values suffice to
    # test each position independently without a six-dimensional large domain.
    base=['k z'+n+'[]' for n in NAMES]
    sequences=['l[a][]','l[a]['+' '.join(base[:-1])+']',SEQ[:-1]+' k zperson[]]']
    for i in range(len(NAMES)):
        changed=base.copy();changed[i]='k z'+('activity' if i%2==0 else 'person')+'[]'
        sequences.append('l[a]['+' '.join(changed)+']')
    for seq in sequences:
        q=fixture('q[t[c[s[k r44w[r[p zmessage]]]]['+seq+' k zref[]]][k zpoint[]]].')
        v,_=model(q,focused=True);assert run(q,v,True)==[False],seq
    reason=fixture('q[t[k zzq[k zperson[] k zactivity[]]][k zpoint[]]].q[t[k r44u[l[a][k zperson[] k zactivity[]] k zref[]]][k zpoint[]]].')
    for variant in ('baseline','missing_cg'):
        v,_=model(reason,variant,focused=True);assert run(reason,v,True)==[variant=='baseline']*2
    return dict(native_direct_adapter_constructed_speech=rows,exact_six_position_bindings=True,
        wrong_length_rejected=True,native_reason_target=True,focused_domain=['one','two'],no_definition_boundaries=True)


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        t=format_graph(new.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    evidence=read(EVIDENCE)
    for p in evidence['pages']:assert digest((ROOT/p['path']).read_bytes())==p['sha256']
    s=evidence['source'];unit=next(u for u in read(evidence['source_inventory'])['units'] if u['id']==s['unit'])
    assert unit['text_sha256']==s['unit_sha256'] and unit['text'][slice(*s['range'])]==s['text']
    assert not new.document['statements']
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        existing_r3z_rhe_r37c_reused=True,no_source_sentence_added=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)


def build_report():
    results={}
    for name,fn in [('candidates',candidate_checks),('norms',norm_checks),('targets',target_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    evidence=read(EVIDENCE)
    paths=set(build())|set(catalog().source_sha256)|set(PRIORS)|{DOC,EVIDENCE,evidence['source_inventory'],*[p['path'] for p in evidence['pages']],
        'scripts/compose_scholarly_own_voice.py','scripts/check_scholarly_own_voice.py','tests/test_scholarly_own_voice.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py',
        'scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py','scripts/compose_confessional_teaching.py'}
    return dict(status='written_public_own_voice_candidates_execution_and_two_freedoms',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
