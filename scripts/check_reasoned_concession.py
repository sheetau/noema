"""Check shared-premise expectation contrasts and their scoped attribution."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_reasoned_concession import ROOT,PARENT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,MEANINGS,REFERENCES,LIMITS,PC,parent,build,closure
from scripts.check_attributed_focus import unwrap

REPORT='reports/reasoned-concession-v1.json'
READING='data/reasoned-concession-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'


def unknown(*args):raise ValueError('Unknown concession input')


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def fixture(roots,suffix):
    doc=deepcopy(catalog().document);doc['declarations']=closure(doc,roots);doc['statements']=[]
    return parse(format_graph(doc,'compact')+suffix)


def evaluate(doc,model,individuals=('observer','first','second','other'),situations=('anchor','elsewhere')):
    return [r['value'] for r in evaluate_document(doc,individuals=individuals,situations=situations,
        primitives={d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=1000000,memoize_definitions=False,memoize_expressions=False)]


def joint_kind(description,premise,outcome):
    """Recognize the two constructed forms, checking both operands and scope."""
    assert description.rank==1
    body=json.loads(description.syntax)
    assert body['kind']=='apply' and body['arguments']==[
        dict(kind='call',symbol=premise,arguments=[]),dict(kind='call',symbol=outcome,arguments=[])]
    fn=body['function'];assert fn['kind']=='lambda' and len(fn['parameters'])==2
    left,right=[x['name'] for x in fn['parameters']]
    content=fn['body'];assert content['kind']=='content'
    scene=dict(kind='variable',name=content['variable'])
    first=dict(kind='evaluate',content=dict(kind='variable',name=left),situation=scene)
    second=dict(kind='evaluate',content=dict(kind='variable',name=right),situation=scene)
    conjunction=content['body'];assert conjunction['kind']=='and' and conjunction['arguments'][0]==first
    tail=conjunction['arguments'][1]
    if tail==second:return 0
    assert tail==dict(kind='not',arguments=[second]);return 1


def ranker(bits=(True,False,True,True),premise='zleft',outcome='zright',observer='observer',anchor='anchor'):
    def ranking(who,left,right,scene):
        i,j=joint_kind(left,premise,outcome),joint_kind(right,premise,outcome)
        return (who,scene)==(observer,anchor) and bits[2*i+j]
    return ranking


@lru_cache(None)
def generic_document():
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zp[d] c.r zq[d] c.r zobserver[] a.r zanchor[] d.r zpoint[] d.
d zleft[] e[b point[k zp[v point]]].d zright[] e[b point[k zq[v point]]].
r zranking[a i b[e] i b[e] d] c.
q[t[s[k rqvq[r b[k zleft[]] r b[k zright[]]]]][k zpoint[]]].
q[t[s[k rqvr[r b[k zleft[]] r b[k zright[]]]]][k zpoint[]]].
q[t[k rqvs[r b[k zleft[]] r b[k zright[]] k zobserver[] k zanchor[] p zranking]][k zpoint[]]].
'''
    return parse(text)


def generic_checks():
    doc=generic_document();count=0
    for p,q in product((False,True),repeat=2):
        for bits in product((False,True),repeat=4):
            model=dict(zp=lambda s:p,zq=lambda s:q,zobserver=lambda:'observer',zanchor=lambda:'anchor',zpoint=lambda:'elsewhere',zranking=ranker(bits))
            actual=evaluate(doc,model);expected=[p and q,p and not q,bits[0] and bits[3] and bits[2] and not bits[1]]
            assert actual==expected,(p,q,bits,actual);count+=1
    # Compare descriptions while their world contents are entirely unknown.
    selected=dict(doc,statements=doc['statements'][-1:]);rows={}
    for variant,ranking in [('strict',ranker()),('tied',ranker((True,True,True,True))),('incomparable',ranker((True,False,False,True))),
        ('reversed',ranker((True,True,False,True))),('other_observer',ranker(observer='other')),('other_anchor',ranker(anchor='elsewhere'))]:
        model=dict(zp=unknown,zq=unknown,zobserver=lambda:'observer',zanchor=lambda:'anchor',zpoint=lambda:'elsewhere',zranking=ranking)
        actual=evaluate(selected,model);assert actual==[variant=='strict'],(variant,actual);rows[variant]=actual
    for name in ('zranking','zobserver','zanchor'):
        model=dict(zp=unknown,zq=unknown,zobserver=lambda:'observer',zanchor=lambda:'anchor',zpoint=lambda:'elsewhere',zranking=ranker());model[name]=unknown
        try:evaluate(selected,model)
        except ValueError as e:assert 'Unknown concession' in str(e)
        else:raise AssertionError(name)
    return dict(world_and_comparison_combinations=count,contrasts=rows,required_unknowns_refused=3,
        world_contents_not_evaluated_for_background=True,same_positive_premise_on_both_sides=True,uncached=True)


def order_checks():
    doc=fixture(['rqvt'],'r zfirst[] a.r zsecond[] a.r zcontext[] d.r zbefore[a a d] c.q[k rqvt[k zfirst[] k zsecond[] k zcontext[] p zbefore]].')
    count=0
    for identical,forward,reverse in product((False,True),repeat=3):
        second='first' if identical else 'second'
        # If the nodes coincide, the two queries are the same relation input.
        m=dict(zfirst=lambda:'first',zsecond=lambda:second,zcontext=lambda:'anchor',
            zbefore=lambda a,b,s:((a,b)==('first',second) and forward) or ((a,b)==(second,'first') and reverse))
        actual=evaluate(doc,m);assert actual==[not identical and forward and not reverse];count+=1
    m['zbefore']=unknown
    try:evaluate(doc,m)
    except ValueError as e:assert 'Unknown concession' in str(e)
    else:raise AssertionError('Unknown order was guessed')
    return dict(cases=count,unknown_order_refused=True)


DOMAIN=('author','previous','low','learn','outcome','contrast','other')
SCENES=('anchor','elsewhere')


@lru_cache(None)
def source_document():return fixture(['hztx'],'q[k ft[]].q[k gy[]].q[k hztx[]].')


def source_model(doc,bits=(True,)*6,variant='baseline'):
    low,learn,outcome,reason,reported,background=bits
    m={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    m.update(wa=lambda:'author',wh=lambda:'anchor',hzsq=lambda:'previous',fu=lambda:'low',fv=lambda:'learn',g2=lambda:'outcome',hztz=lambda:'contrast')
    def same(author,scene):return (author,scene)==('other' if variant=='other_author' else 'author','elsewhere' if variant=='other_context' else 'anchor')
    def claim(node,author,content,scene):
        expected={'low':('e4',low),'learn':('fs',learn),'outcome':('gx',outcome)}
        if node not in expected:return False
        symbol,flag=expected[node]
        if variant=='swapped_claims' and node in ('low','learn'):symbol='fs' if node=='low' else 'e4'
        return same(author,scene) and flag and json.loads(content.syntax)==dict(kind='call',symbol=symbol,arguments=[])
    def inference(author,premises,conclusion,scene):
        selected={x for x in DOMAIN if premises(x)}
        return reason and same(author,scene) and (selected,conclusion)==(
            ({'low'},'learn') if variant=='reversed_reason' else ({'learn','other'},'low') if variant=='extra_premise' else ({'learn'},'low'))
    def order(first,second,scene):
        pairs={('previous','low'),('low','learn'),('learn','outcome')}
        if variant=='missing_prior_link':pairs.remove(('previous','low'))
        if variant=='reversed_learning':pairs.remove(('low','learn'));pairs.add(('learn','low'))
        if variant=='both_directions':pairs.add(('outcome','learn'))
        return scene=='anchor' and (first,second) in pairs
    def report(node,author,content,scope,scene):
        return reported and same(author,scene) and (node,scope)==('outcome','other' if variant=='other_foreground_scope' else 'outcome') and \
            unwrap(content)==dict(kind='call',symbol='gx',arguments=[])
    def bg(node,author,fg,bg,fs,bs,scene):
        wanted=('hztv','gx') if variant=='swapped_background' else ('gx','hztv')
        return background and same(author,scene) and (node,fs,bs)==(
            'other' if variant=='other_node' else 'outcome','outcome','other' if variant=='other_background_scope' else 'contrast') and \
            [unwrap(fg),unwrap(bg)]==[dict(kind='call',symbol=n,arguments=[]) for n in wanted]
    m.update(uc=claim,ud=inference,ue=order,hznreport=report,hzrbgreport=bg)
    return m


def attribution_checks():
    doc=source_document();count=0
    for bits in product((False,True),repeat=6):
        actual=evaluate(doc,source_model(doc,bits),DOMAIN,SCENES)
        assert actual==[bits[0] and bits[1] and bits[3],bits[2],all(bits)],(bits,actual);count+=1
    selected=dict(doc,statements=doc['statements'][-1:]);rows={}
    for variant in ('baseline','other_author','other_context','swapped_claims','reversed_reason','extra_premise','missing_prior_link',
        'reversed_learning','both_directions','other_foreground_scope','other_background_scope','other_node','swapped_background'):
        actual=evaluate(selected,source_model(doc,variant=variant),DOMAIN,SCENES)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
    for name in ('uc','ud','ue','hznreport','hzrbgreport'):
        m=source_model(doc);m[name]=unknown
        try:evaluate(selected,m,DOMAIN,SCENES)
        except ValueError as e:assert 'Unknown concession' in str(e)
        else:raise AssertionError(name)
    # The background is not guessed even when another attribution is false.
    m=source_model(doc,(False,True,True,True,True,True));m['hzrbgreport']=unknown
    try:evaluate(selected,m,DOMAIN,SCENES)
    except ValueError as e:assert 'Unknown concession' in str(e)
    else:raise AssertionError('False claim concealed unknown background attribution')
    return dict(attribution_combinations=count,contrasts=rows,required_unknowns_refused=5,
        world_and_expectation_inputs_unknown=True,false_claim_does_not_hide_unknown_background=True,uncached_current_runtime=True)


def native_background_checks():
    doc=fixture(['hztv'],'r za[] d.q[t[k hztv[]][k za[]]].');rows={}
    for variant,ranking in [('strict',ranker(premise='e4',outcome='gx',observer='author')),
        ('tied',ranker((True,True,True,True),'e4','gx','author')),
        ('incomparable',ranker((True,False,False,True),'e4','gx','author')),
        ('reversed',ranker((True,True,False,True),'e4','gx','author')),
        ('other_view',ranker(premise='e4',outcome='gx',observer='other')),
        ('other_scene',ranker(premise='e4',outcome='gx',observer='author',anchor='elsewhere'))]:
        m={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        m.update(wa=lambda:'author',za=lambda:'anchor',hzpt=ranking)
        actual=evaluate(doc,m,DOMAIN,SCENES);assert actual==[variant=='strict'],(variant,actual);rows[variant]=actual
    m['hzpt']=unknown
    try:evaluate(doc,m,DOMAIN,SCENES)
    except ValueError as e:assert 'Unknown concession' in str(e)
    else:raise AssertionError('Unknown expectation became a contrast')
    return dict(cases=rows,same_e4_and_gx_on_both_sides=True,unknown_world_not_evaluated=True,unknown_ranking_refused=True)


def structure():
    old=parent();new=catalog();assert new.document['declarations'][:-8]==old.document['declarations']
    assert all(new.entries[n]==entry for n,entry in old.entries.items())
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==38
    assert new.document['statements'][-1]==dict(kind='assert',body=dict(kind='call',symbol='hztx',arguments=[]))
    used={d['name'] for d in closure(new.document,['hztx'])}
    assert {'ft','gy','e4','fs','gx','rqvs','rqvq','rqvr','rqts','rqtr','rqtq','hznreport','hzrbgreport','rqtv','hzpt'}<=used
    idx=json.loads((ROOT/'data/semantic-review-index-v30.json').read_text(encoding='utf-8'))
    for path in idx['works']['kant-1784']['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[s['index'] for s in review['selection']['statements']]
        assert selection_binding(old,indices)==review['selection']==selection_binding(new,indices)
    for path in (FULL,CORE,LIBRARY):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('full','compact'):
            text=format_graph(d,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    assert all(d['kind']=='definition' for d in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
    return dict(new_definitions=7,new_semantic_primitive_relations=0,new_local_references=1,appended_statement_indices=[37],
        other_statements_preserved=37,nine_review_bindings_preserved=True,generic_library_has_no_source_primitives=True,roundtrips=True)


def source_record():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    start=unit['text'].index('Nun ist diese Gefahr');end=len(unit['text'])
    return dict(status='explicit_reason_and_joint_scenario_expectation_reading',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,end],text=unit['text'][start:end]),
        references=['https://korpora.org/Kant/aa08/035.html','https://korpora.org/Kant/aa08/036.html',
            'https://grammis.ids-mannheim.de/systematische-grammatik/2109','https://grammis.ids-mannheim.de/systematische-grammatik/366'],
        decision='危険の程度Pを学習の見込みで理由付け、例による萎縮・通常の回避Qを、Pかつ非Qより見込まれにくいPかつQとして提示する部分的な読解を採る。',
        reasoning='原文のzwar、理由を示すdenn、後続のalleinとdochを同じ文の構造として読む。IDSの譲歩に関する一般説明は通常の見込みからの例外を区別するが、この原文の比較対象や作用範囲を一意に指定するものではない。質的な二候補比較は今回選ぶ操作化である。',
        limits=LIMITS,whole_unit_semantically_verified=False,binding=selection_binding(catalog(),[37]),
        source_sha256={INVENTORY:digest((ROOT/INVENTORY).read_bytes())})


def build_report():
    for p,text in build().items():assert (ROOT/p).read_text(encoding='utf-8')==text,p
    results={}
    for name,fn in [('generic',generic_checks),('order',order_checks),('attribution',attribution_checks),('native_background',native_background_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    reading=source_record();assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==reading;s=reading['source']
    prior=json.loads((ROOT/'reports/careful-prevention-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,prior['source_sha256'])
    # Historical reports supply ranges, not current-runtime semantic evidence.
    historical=['reports/directed-presentations-v1.json','reports/experience-acquisition-v1.json','reports/example-deterrence-v1.json']
    previous=[json.loads((ROOT/p).read_text(encoding='utf-8'))['alignment'] for p in historical]
    ranges=[next(x for x in previous[0]['segments'] if x['start']==s['range'][0]),previous[1],previous[2]]
    assert [(r['start'],r['end']) for r in ranges]==[(1213,1257),(1259,1324),(1326,1438)]
    segments=[]
    for r in ranges:
        start,end=r['start'],r['end'];source=s['text'][start-s['range'][0]:end-s['range'][0]]
        assert source==r['source']
        segments.append(dict(start=start,end=end,source=source,definitions=list(MEANINGS),
            status='partial_reason_and_expectation_attribution',full_semantic_equivalence=False))
    alignment=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],segments=segments)
    paths=set(build())|set(catalog().source_sha256)|set(prior['source_sha256'])|set(reading['source_sha256'])|set(historical)|{READING,
        'reports/careful-prevention-v1.json','scripts/compose_scalar_backgrounds.py','scripts/check_attributed_focus.py',
        'scripts/compose_reasoned_concession.py','scripts/check_reasoned_concession.py','tests/test_reasoned_concession.py','docs/reasoned-concession-v1.md'}
    return dict(status='reason_and_counterexpectation_connected_as_distinct_attributions',document=FULL,**results,alignment=alignment,
        verified_full_units={'kant-1784':0,'einstein-1905':0},new_covered_characters=0,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(source_record()));report=build_report()
    if args.verify_only:assert json.loads((ROOT/REPORT).read_text(encoding='utf-8'))==report
    else:write_exact(ROOT/REPORT,encoded(report))
    print('Reason, counterexpectation and scoped attribution checked',flush=True)


if __name__=='__main__':main()
