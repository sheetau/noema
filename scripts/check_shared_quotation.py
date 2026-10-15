"""Verify shared quoted frames, plural obligations and source attribution."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import argparse,hashlib,json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from scripts.compose_shared_quotation import ROOT,PARENT,LIBRARY,SOURCE,CORE,BASIS,CHOICES,OBEDIENCE,FIELDS,PERMISSION,OBEY,SEQUENCE,build,basis
from scripts.compose_origin_clock import definition

REPORT=ROOT/'reports/shared-quotation-v1.json'
DOMAIN=('p','q','x','y','c','d','e','f')
SCENES=('anchor','later')

@lru_cache(maxsize=2)
def setup(restricted=False):
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8'));text=format_graph(doc,'compact')
    for n,t in FIELDS:
        if n=='targets' or n=='descriptions':continue
        if t.startswith('h['):text+='r jq'+n+'['+t[2:t.rfind(']')]+'] '+t[t.rfind(']')+1:].strip()+'.'
        else:text+='r jq'+n+'[] '+t+'.'
    text+='r jqlater[] d.r jqexec[a a d] c.'
    text+=definition('jqaction','person a activity a','b point[k jqexec[v person v activity v point]]','e')
    text+=definition('jqalias','person a activity a','b point[k jqexec[v person v activity v point]]','e')
    for name in ('targets','descriptions'):text+=definition('jq'+name,'person a item a anchor d','r[p jqaction]','i[h[a a] e]')
    refs={n:('p jq'+n if t.startswith('h[') else 'k jq'+n+'[]') for n,t in FIELDS}
    policy='k rub['+' '.join(refs[n] for n,_ in PERMISSION)+']'
    compliance='k rua['+' '.join(refs[n] for n,_ in OBEY)+']'
    quoted='k ruc['+' '.join('r b['+refs[n]+']' for n,_ in FIELDS)+']'
    literal='l[i b[f]][r b[c[i[content e][j s[v content]]][c[p rub]['+' '.join(refs[n] for n,_ in PERMISSION)+']]] r b[c[i[content e][j m[v content]]][c[p rua]['+' '.join(refs[n] for n,_ in OBEY)+']]]]'
    text+='q[t['+policy+'][k jqanchor[]]].q[t['+compliance+'][k jqlater[]]].q[e['+quoted+']['+literal+']].'
    doc=parse(text)
    if restricted:
        prefix=[d for d in doc['declarations'] if d['kind']=='primitive' or d['name'] in ('jqaction','jqalias')]
        doc['declarations']=prefix+[d for d in doc['declarations'] if d not in prefix]
        node=next(d for d in doc['declarations'] if d['name']=='rtx')['body']['body']['body']
        assert node['kind']=='forall' and node['sort']['kind']=='description'
        instances=[dict(kind='apply',function=dict(kind='lambda',parameters=[dict(name=node['variable'],sort=deepcopy(node['sort']))],body=deepcopy(node['body'])),
            arguments=[dict(kind='quote',body=dict(kind='function_ref',symbol=symbol))]) for symbol in ('jqaction','jqalias')]
        node.clear();node.update(kind='and',arguments=instances)
        doc=parse(format_graph(doc,'compact'))
    return doc

def values(permissions=(True,True),execution=(True,True),*,people=('p','q'),variant='baseline',indices=(0,1,2),restricted=True,memoize=True):
    doc=deepcopy(setup(restricted));doc['statements']=[doc['statements'][i] for i in indices]
    def forbidden(*args):raise AssertionError('Unknown content executed while constructing quotation')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def population(person,point):return person in people and point=='anchor'
    def required(source,person,role,activity,code,sign,point):
        if variant=='unknown_requirements':raise ValueError('Unknown requirements')
        if variant=='missing_person_command' and person=='p':return False
        expected='jqalias' if variant=='other_description' else 'jqaction'
        source_expected='c' if variant=='other_source' else 'x'
        context='later' if variant=='other_anchor' else 'anchor'
        return (source,role,point)==(source_expected,'y',context) and person in people and \
            (activity,sign) in (('e',True),('f',False)) and json.loads(code.syntax)==dict(kind='function_ref',symbol=expected)
    def allowed(source,person,role,activity,code,sign,point):
        if variant=='unknown_permissions':raise ValueError('Unknown permissions')
        return (source,role,activity,sign)==('x','y','e',True) and person in people and permissions[('p','q').index(person)] and \
            json.loads(code.syntax)==dict(kind='function_ref',symbol='jqaction')
    def actual(person,activity,point):
        if variant=='unknown_execution':raise ValueError('Unknown execution')
        return person in people and activity=='e' and execution[('p','q').index(person)]
    model.update(jqsource=lambda:'x',jqanchor=lambda:'anchor',jqlater=lambda:'later',jqpeople=population,
        jqtopics=lambda person,topic,point:population(person,point) and topic=='c',
        jqextents=lambda person,extent,point:population(person,point) and extent=='d',
        jqcandidates=lambda person,act,point:population(person,point) and act=='e',
        jqsubject=lambda person,act,point:'c',jqextent=lambda person,act,point:'d',jqroles=lambda person,act,point:'y',
        jqrolescope=lambda person,role,point:population(person,point) and role=='y',
        jqitems=lambda person,item,point:population(person,point) and item in ('c','d') and not (variant=='omitted_person_records' and person=='p'),
        jqorderroles=lambda person,item,point:'y',jqactions=lambda person,item,point:'e' if item=='c' else 'f',
        jqsigns=lambda person,item,point:item=='c',jqrequired=required,jqallowed=allowed,jqexec=actual)
    return [row['value'] for row in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=model,
        max_steps=50_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]

@lru_cache(maxsize=2)
def source_setup(path=CORE):
    doc=parse((ROOT/path).read_text(encoding='utf-8'));doc['statements']=[]
    text=format_graph(doc,'compact')+'r jqspeaker[] a.r jqaudience[a d] c.r jqcontext[] d.'
    refs={n:'p hzs'+n for n,_ in FIELDS};refs.update(source='k jqspeaker[]',people='p jqaudience',anchor='k jqcontext[]',required='p h7a',allowed='p h7b')
    literal='l[i b[f]][r b[c[i[content e][j s[v content]]][c[p rub]['+' '.join(refs[n] for n,_ in PERMISSION)+']]] r b[c[i[content e][j m[v content]]][c[p rua]['+' '.join(refs[n] for n,_ in OBEY)+']]]]'
    text+='q[e[k hzsquotation[r b[k jqspeaker[]] r b[p jqaudience] r b[k jqcontext[]]]]['+literal+']].'
    return parse(text)

def source_construction(path=CORE):
    doc=source_setup(path)
    def forbidden(*args):raise AssertionError('Source quotation construction executed a primitive')
    return [row['value'] for row in evaluate_document(doc,individuals=('person',),situations=('context',),
        primitives={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'},max_steps=1_000_000)]

def attribution(path=CORE,reported=True,variant='baseline'):
    doc=deepcopy(parse((ROOT/path).read_text(encoding='utf-8')));doc['statements']=doc['statements'][-1:]
    def forbidden(*args):raise AssertionError('Attribution executed its quoted template')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    def report(node,author,template,scope,context):
        expected=['node','author','scope','context']
        if variant in ('node','author','scope','context'):expected[('node','author','scope','context').index(variant)]='other'
        return reported and [node,author,scope,context]==expected and template.rank==2 and json.loads(template.syntax)==dict(kind='function_ref',symbol='hzsquotation')
    model.update(hzsnode=lambda:'node',wa=lambda:'author',hzsscope=lambda:'scope',wh=lambda:'context',hzsreport=report)
    return [row['value'] for row in evaluate_document(doc,individuals=('node','author','scope','other'),situations=('context','other'),primitives=model)]

@lru_cache(maxsize=1)
def field_setup():
    from scripts.compose_shared_quotation import FIELD_SYMBOLS
    from scripts.compose_public_permission_risk import INPUTS
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));doc['statements']=[]
    prefix='p:r jqrole[] a.r jqtopic[] a.r jqother[] a.r jqrecipient[] a.r jqchannel[] a.r jqperson[] a.r jqactivity[] a.r jqanchor[] d.'
    prefix+='r jqreaders[a] c.r jqmessage[a] f.r jqvoices[a a a a a i[h[a] f] d] c.'
    extra=parse(prefix)
    codes={'role':'r[k jqrole[]]','audience':'r[p jqreaders]','subject':'r[k jqtopic[]]',
           'message':'r[p jqmessage]','recipient':'r[k jqrecipient[]]','channel':'r[k jqchannel[]]','voices':'r[p jqvoices]'}
    replacements={}
    for name,t in INPUTS:
        replacement=parse(prefix+definition(FIELD_SYMBOLS[name],'person a activity a anchor d',codes[name],t))['declarations'][-1]
        replacements[FIELD_SYMBOLS[name]]=replacement
    doc['declarations']=extra['declarations']+[replacements.get(d['name'],d) for d in doc['declarations']]
    args='k jqperson[] k jqactivity[] k jqanchor[]'
    target='r[c[p rrh][k jqrole[] p jqreaders k jqtopic[] r[p jqmessage] k jqrecipient[] k jqchannel[] p jqvoices]]'
    return parse(format_graph(doc,'compact')+'q[e[k hzsroles['+args+']][k jqrole[]]].q[e[k hzssubject['+args+']][k jqtopic[]]].q[e[k hzstargets['+args+']]['+target+']].')

def source_fields(variant='baseline',indices=(0,1,2)):
    from scripts.compose_shared_quotation import FIELD_SYMBOLS
    doc=deepcopy(field_setup())
    if variant in ('other_role','other_topic'):
        name=FIELD_SYMBOLS['role' if variant=='other_role' else 'subject']
        next(d for d in doc['declarations'] if d['name']==name)['body']['body']['symbol']='jqother'
        doc=parse(format_graph(doc,'compact'))
    doc['statements']=[doc['statements'][i] for i in indices]
    def forbidden(*args):raise AssertionError('A public reasoning action was executed during target construction')
    model={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    model.update(jqrole=lambda:'role',jqtopic=lambda:'topic',jqother=lambda:'other',jqperson=lambda:'person',
        jqactivity=lambda:'activity',jqanchor=lambda:'anchor')
    if variant=='unknown_role':
        def unknown():raise ValueError('Unknown role reference')
        model['jqrole']=unknown
    return [r['value'] for r in evaluate_document(doc,individuals=('role','topic','other','person','activity'),situations=('anchor',),primitives=model)]

def alignment():
    units=json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit=next(u for u in units['units'] if u['id']=='kant-1784:u0017');text=unit['text']
    segments=[]
    for phrase in ('räsonnirt so viel ihr wollt, und worüber ihr wollt','gehorcht'):
        start=text.index(phrase);segments.append(dict(start=start,end=start+len(phrase),text=phrase))
    return dict(work='kant-1784',unit=unit['id'],text_sha256=unit['text_sha256'],segments=segments,
        definitions=['rua','rub','ruc','hzstargets','hzsquotation','hzsattribution'],status='explicit_interpretive_annotation',semantic_completion=False)

def build_report():
    documents={}
    for name,text in build().items():
        assert (ROOT/name).read_text(encoding='utf-8')==text
        doc=parse(text)
        for notation in ('full','compact'):
            form=format_graph(doc,notation);assert parse(form)==doc and parse(transcribe(form,alphabet='v2'))==doc
        documents[name]=dict(declarations=len(doc['declarations']),statements=len(doc['statements']),characters=len(text))
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'));child=parse((ROOT/SOURCE).read_text(encoding='utf-8'))
    assert child['declarations'][:len(parent['declarations'])]==parent['declarations']
    assert child['statements'][:-1]==parent['statements']
    assert json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis()
    matrix=[]
    for a,b,c,d in product((False,True),repeat=4):
        result=values((a,b),(c,d));assert result==[a and b,c and d,True]
        matrix.append(dict(permissions=[a,b],execution=[c,d],result=result))
    contrasts={}
    for name in ('missing_person_command','other_description','other_source','other_anchor','omitted_person_records'):
        result=values(variant=name);assert result==[True,False,True];contrasts[name]=result
    for name in ('unknown_requirements','unknown_permissions','unknown_execution'):
        assert values(variant=name,indices=(2,),restricted=False)==[True]
    try:values(indices=(1,),restricted=False)
    except ValueError as error:assert 'description domain' in str(error)
    else:raise AssertionError('Full description domain silently narrowed')
    assert values(memoize=False,indices=(0,2))==[True,True]
    source_checks={}
    for path in (SOURCE,CORE):
        assert source_construction(path)==[True]
        assert attribution(path)==[True] and attribution(path,False)==[False]
        for variant in ('node','author','scope','context'):assert attribution(path,variant=variant)==[False]
        source_checks[path]=dict(construction_without_execution=True,scoped_attribution=True)
    fields={v:source_fields(v) for v in ('baseline','other_role','other_topic')}
    assert fields=={'baseline':[True,True,True],'other_role':[False,True,False],'other_topic':[True,False,False]}
    assert source_fields('unknown_role',indices=(2,))==[True]
    paths=[PARENT,LIBRARY,SOURCE,CORE,BASIS,CHOICES,OBEDIENCE,'scripts/compose_shared_quotation.py','scripts/check_shared_quotation.py','tests/test_shared_quotation.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py','noema/guarded_ranked_semantics.py','artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_quoted_template_not_full_paragraph',documents=documents,parent_preserved=True,roundtrips=True,
        finite_interpretation=dict(matrix=matrix,contrasts=contrasts,restricted_descriptions=['jqaction','jqalias'],full_description_domain_refused=True,full_description_domain_verified=False),
        source_checks=source_checks,source_field_checks=fields,source_alignment=alignment(),verified_full_units={'kant-1784':0,'einstein-1905':0},unresolved=basis()['unresolved'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})

def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print('Shared speaker, audience, plural compliance and attributed source quotation verified')

if __name__=='__main__':main()
