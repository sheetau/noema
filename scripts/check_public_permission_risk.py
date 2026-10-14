"""Check the actual source policy, its prospective outcomes, and attribution."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import argparse
import hashlib
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts.compose_public_permission_risk import ROOT, PARENT, SOURCE, CORE, BASIS, INPUTS, FIELD_SYMBOLS, build, basis
from scripts.compose_limits import call as k

REPORT=ROOT/'reports/public-permission-risk-v1.json'
DOMAIN=('ruler','person','other','act','role','world','topic','channel','reader','faculty')
SCENES=('anchor','safe','bad','outside')
MESSAGE='r[i[subject a][j s[b point[e[n p a b][n p a b]]]]]'
FALSE_TARGET='r[i[person a activity a][b point[u[e[n p a b][n p a b]]]]]'


@lru_cache(maxsize=1)
def setup():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8')); doc['statements']=[]
    args={n:'r[k jd'+n+'[]]' for n in ('role','subject','recipient','channel')}
    args.update(audience='r[p jdaudience]',voices='r[p jdvoices]',message=MESSAGE)
    target=k('rri',*(args[n] for n,_ in INPUTS))
    text='r jdrole[] a.r jdsubject[] a.r jdrecipient[] a.r jdchannel[] a.r jdaudience[a] c.'
    text+='r jdvoices[a a a a a i[h[a] f] d] c.r jdperson[] a.r jdactivity[] a.'
    text+='r jdcapture['+' '.join(t for _,t in INPUTS)+'] c.'
    text+='r jdtargets[i[h[a a] e] i[h[a a] e]] c.r jdpolicy[i b[e]] c.'
    queries=[k('jdcapture',*(args[n] for n,_ in INPUTS)),k('jdtargets',target,FALSE_TARGET),k('jdpolicy',k('hzmpolicy')),
        k('rrl',k('hzmpolicy'),k('wh'),'p hzmprospects')]
    queries += [k(n,k('hzmpolicy'),k('wh'),'p hzmprospects','p hzmadverse') for n in ('rrm','rrn')]
    queries += ['t[s[r c[k hzmsafety[]]]][k wh[]]',
        't[c[s['+target+']][k jdperson[] k jdactivity[]]][k wh[]]',
        't[s[k hzmpolicy[]]][k wh[]]']
    doc=parse(format_graph(doc,'compact')+text+''.join('q['+q+'].' for q in queries))
    return dict(document=doc,arguments=args,target=target)


def model_for(data, selected=('safe',), grants=(True,True), harm=True, performed=False, actual_grant=False, variant='baseline'):
    stored={}
    def forbidden(*args): raise ValueError('Unspecified interpretation executed')
    model={d['name']:forbidden for d in data['document']['declarations'] if d['kind']=='primitive'}
    def capture(*values): stored.update(zip((n for n,_ in INPUTS),values)); return True
    def targets(target,alias): stored.update(target=target,alias=alias); return True
    def policy(value): stored['policy']=value; return True
    def prospects(code,anchor,point):
        if variant=='unknown_prospects': raise ValueError('Policy prospects are unknown')
        return anchor=='anchor' and point in selected and code.syntax==stored['policy'].syntax and variant!='wrong_policy'
    def adverse(point):
        if variant=='unknown_harm': raise ValueError('Adverse outcome is unknown')
        return (point=='bad' and harm) or point=='outside'
    def allowed(ruler,person,role,act,desc,sign,point):
        if (ruler,role,act,sign)!=('other' if variant=='wrong_ruler' else 'ruler','other' if variant=='wrong_role' else 'role','act',True): return False
        if desc.syntax!=stored['alias' if variant=='wrong_target' else 'target'].syntax: return False
        if person not in ('person','other'): return False
        if variant=='second_person_unpermitted' and person=='other': return False
        return dict(safe=grants[0],bad=grants[1],anchor=actual_grant,outside=False)[point]
    def required(ruler,person,role,act,desc,sign,point):
        return variant=='conflict' and (ruler,person,role,act,sign)==('ruler','person','role','act',False) and point in selected and desc.syntax==stored['target'].syntax
    def conveys(act,reader,topic,desc,point):
        return performed and (act,reader,topic,point)==('act','reader','topic','anchor') and desc.syntax==stored['message'].syntax
    model.update(jdcapture=capture,jdtargets=targets,jdpolicy=policy,
        jdrole=lambda:'role',jdsubject=lambda:'topic',jdrecipient=lambda:'world',jdchannel=lambda:'channel',
        jdperson=lambda:'person',jdactivity=lambda:'act',jdaudience=lambda reader:reader=='reader',
        jdvoices=lambda person,act,principal,role,topic,desc,point:(person,act,principal,role,topic,point)==('person','act','person','role','topic','anchor') and desc.syntax==stored['message'].syntax,
        hzmruler=lambda:'ruler',wh=lambda:'anchor',
        hzmpeople=lambda person,point:point=='anchor' and (person=='person' or (variant=='second_person_unpermitted' and person=='other')),
        hzmactivities=lambda person,act,point:act=='act' and point=='anchor',
        hzmprospects=prospects,hzmadverse=adverse,h7a=required,h7b=allowed,
        ab=lambda faculty,person,point:(faculty,person)==('faculty','person'),
        ac=lambda person,faculty,act,point:performed and (person,faculty,act,point)==('person','faculty','other' if variant=='other_use_activity' else 'act','anchor'),
        dg=lambda act,point:performed and (act,point)==('act','anchor'),f3=lambda person,act,point:(person,act,point)==('person','act','anchor'),f2=conveys,
        ca=lambda person,act,point:(person,act,point)==('person','act','anchor'),
        cb=lambda person,act,role,point:(person,act,role,point)==('person','act','role','anchor'),
        cc=lambda act,recipient,point:(act,recipient,point)==('act','world','anchor'),
        cd=lambda role,point:role=='role',ce=lambda recipient,point:recipient=='world',
        aa=lambda person:person in ('person','reader'),h6n=lambda reader,point:reader=='reader',
        h6t=lambda recipient,reader,point:(recipient,reader)==('world','reader'),
        h6u=lambda act,channel,topic,desc,point:channel=='channel' and (act,topic,point)==('act','topic','anchor') and desc.syntax==stored['message'].syntax)
    for name,symbol in FIELD_SYMBOLS.items(): model[symbol]=lambda person,act,anchor,name=name:stored[name]
    return model


def values(indices=None,**options):
    data=setup()
    if indices is not None:
        data={**data,'document':deepcopy(data['document'])}
        data['document']['statements']=[data['document']['statements'][i] for i in indices]
    return [r['value'] for r in evaluate_document(data['document'],individuals=DOMAIN,situations=SCENES,primitives=model_for(data,**options),max_steps=8_000_000)]


def attribution(doc):
    selected=deepcopy(doc); selected['statements']=selected['statements'][-1:]
    rows=[]
    for granted in (False,True):
        def forbidden(*args): raise ValueError('Attribution executed the risk content')
        def attributed(node,author,content,scope,point):
            assert (node,author,scope,point)==('node','author','scope','point')
            assert content.rank==2 and json.loads(content.syntax)=={'kind':'call','symbol':'hzmsafety','arguments':[]}
            return granted
        model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
        model.update(hzmreport=attributed,hzmnode=lambda:'node',wa=lambda:'author',hzmscope=lambda:'scope',wh=lambda:'point')
        result=evaluate_document(selected,individuals=('node','author','scope'),situations=('point',),primitives=model)
        assert result==[{'kind':'assert','value':granted}]; rows.append(result)
    return rows


def build_report():
    texts=build(); assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    documents={}
    for path,text in texts.items():
        assert (ROOT/path).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[path]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text),attribution=attribution(doc))
    parent,source=[parse((ROOT/p).read_text(encoding='utf-8')) for p in (PARENT,SOURCE)]
    assert source['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert source['statements'][:-1]==parent['statements']
    matrix=[]
    for safe_selected,bad_selected,safe_grant,bad_grant in product((False,True),repeat=4):
        selected=tuple(p for p,b in (('safe',safe_selected),('bad',bad_selected)) if b)
        coherent=bool(selected) and (not safe_selected or safe_grant) and (not bad_selected or bad_grant)
        expected=[True]*3+[coherent,coherent and not bad_selected,coherent and bad_selected,coherent and not bad_selected,False,False]
        result=values(selected=selected,grants=(safe_grant,bad_grant))
        assert result==expected,(selected,result,expected)
        matrix.append(dict(selected=list(selected),grants=[safe_grant,bad_grant],result=result))
    contrasts={}
    for variant in ('wrong_policy','wrong_ruler','wrong_role','wrong_target','conflict','second_person_unpermitted'):
        result=values(variant=variant)
        assert result==[True]*3+[False]*6,(variant,result)
        contrasts[variant]=result
    source_unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0016')
    phrase='es ohne Gefahr sei, seinen Unterthanen zu erlauben, von ihrer eigenen Vernunft öffentlichen Gebrauch zu machen'
    start=source_unit['text'].index(phrase)
    paths=[PARENT,SOURCE,CORE,BASIS,'scripts/compose_public_permission_risk.py','scripts/check_public_permission_risk.py',
        'tests/test_public_permission_risk.py','scripts/compose_speech_principals.py','scripts/compose_described_norms.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py',
        'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_public_permission_risk_source_connection',documents=documents,preserved_parent=True,new_author_fragment_attributions=1,
        finite_interpretation=dict(matrix=matrix,contrasts=contrasts),roundtrips=True,
        alignment=dict(semantic_completion=False,segments=[dict(unit=source_unit['id'],unit_sha256=source_unit['text_sha256'],
            range=[start,start+len(phrase)],text=phrase,status='explicit_interpretive_annotation',definitions=['rrh','rri','rrj','rrk','rrl','rrm','hzmpolicy','hzmsafety','hzmriskreport'])]),
        limitations=basis()['unresolved'],verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    result=build_report()
    if args.verify_only: assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Same policy, prospective permission, adverse outcomes and source attribution verified')


if __name__=='__main__':main()
