"""One shared interpretation for the stored Kant qualification chain."""
from copy import deepcopy
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,Content,FunctionValue,SequenceValue
from noema.diagnostic_short_circuit import lower
from scripts import check_supported_apprehension as speech
from scripts import check_protective_qualification as protection
from scripts import check_armed_readiness as armed
from scripts.compose_qualified_utterance import closure
from scripts.compose_armed_readiness import ROOT,SOURCE

REPORT=ROOT/'reports/integrated-qualification-v1.json'
COMPONENTS=('ready','assigned','protected','owned','supported','mapped','remaining')
CONTRASTS=('different_members','different_assigned_community','different_protected_community','different_commander')
UNKNOWNS=('unknown_mission','unknown_protection','unknown_remaining','unknown_mapping')


def capture(module,call):
    captured={}
    def receive(doc,**kwargs):captured.update(document=deepcopy(doc),**kwargs);return []
    with patch.object(module,'evaluate_document',side_effect=receive):call()
    assert captured
    return captured


class Bridge:
    """Rename fixture individuals and lift their finite content to shared scenes."""
    def __init__(self,rename,scenes):
        self.forward=dict(rename);self.backward={v:k for k,v in rename.items()};assert len(self.backward)==len(rename)
        self.scenes=tuple(scenes);self.functions={}

    def value(self,value,forward=True):
        mapping=self.forward if forward else self.backward
        if isinstance(value,str):return mapping.get(value,value)
        if isinstance(value,FunctionValue):
            key=(value,forward)
            if key not in self.functions:
                self.functions[key]=FunctionValue(value.parameters,value.result,
                    lambda *args:self.value(value(*(self.value(a,not forward) for a in args)),forward))
            return self.functions[key]
        if isinstance(value,SequenceValue):return SequenceValue(tuple(self.value(v,forward) for v in value.items),value.element_type)
        if isinstance(value,Content):
            points=tuple(self.value(p,forward) for p in value.situations)
            table=dict(zip(points,value.values,strict=True))
            # Only the fixture's supplied threat contents cross this boundary.
            # New scenes explicitly have no threat in the combined interpretation.
            domain=self.scenes if forward else points
            return Content(domain,tuple(table.get(p,False) for p in domain))
        return value

    def callback(self,fn):return lambda *args:self.value(fn(*(self.value(a,False) for a in args)))


def fixture(*,ready=True,assigned=True,protected=True,owned=True,supported=True,mapped=True,success=True,remaining=True,variant='baseline'):
    s=capture(speech,lambda:speech.source_values(owned=owned,supports=supported,mapped=mapped,success=success,indices=(0,)))
    p=capture(protection,lambda:protection.values(flags=(True,True,protected),indices=(0,)))
    a=capture(armed,lambda:armed.source_values(ready=ready,assigned=assigned,indices=(3,)))
    scenes=tuple(dict.fromkeys([*s['situations'],*p['situations'],*a['situations']]))
    pb=Bridge({'chief':'speaker','m1':'operator','people':'community','plan':'protectplan','other':'protectother'},scenes)
    ab=Bridge({'chief':'speaker'},scenes)
    individuals=tuple(dict.fromkeys(['group',*s['individuals'],*(pb.value(x) for x in p['individuals']),*(ab.value(x) for x in a['individuals'])]))
    doc=deepcopy(s['document']);doc['statements']=[];lookup={d['name']:d for d in doc['declarations']}
    replacements={'rtx':next(d for d in p['document']['declarations'] if d['name']=='rtx')}
    source=parse((ROOT/SOURCE).read_text(encoding='utf-8'))
    for declarations in (p['document']['declarations'],a['document']['declarations'],closure(source,['hzzonly'])):
        for d in declarations:
            if d['name'] not in lookup:doc['declarations'].append(deepcopy(d));lookup[d['name']]=d
            elif d['name'] not in ('rtx','rvy','hzxtasks','hzxcommandcodes','hztcontextfor','hzthearersfor','hztspeakerfor'):
                assert d==lookup[d['name']],d['name']
    doc['declarations']=[deepcopy(replacements.get(d['name'],d)) for d in doc['declarations']]
    # The two description quantifiers remain finite diagnostics, exactly as in
    # the predecessor fixtures. All semantic qualification functions are kept.
    prefix=closure(doc,['jnact','jnalias'])
    names={d['name'] for d in prefix};doc['declarations']=prefix+[d for d in doc['declarations'] if d['name'] not in names]
    text=format_graph(doc,'compact')+'r jiremaining[a a a d] c.'
    expression='k hzzonly[p jiremaining k juanchor[]]'
    questions=[expression,'e[r c['+expression+']][r c['+expression+']]',
        'k hzxgroup[k juperson[] k jggroup[] k juanchor[]]',
        't[k hzzmission[k jggroup[] k jccommunity[]]][k juanchor[]]',
        'k hzyformation[r[p hzzmission] k juperson[] k jggroup[] k jccommunity[] k juanchor[]]',
        't[k h4l[k juperson[]]][k juanchor[]]','t[k hzwtarget[k juperson[]]][k juanchor[]]']
    doc=parse(text+''.join('q['+x+'].' for x in questions))
    model=dict(s['primitives'])
    model.update({n:pb.callback(fn) for n,fn in p['primitives'].items()})
    # Preserve protective selectors: the armed fixture's selector only covered
    # one member and was never meant to replace the protection population.
    model.update({n:ab.callback(fn) for n,fn in a['primitives'].items() if n!='hzxmembersof'})
    membership=model['hzzmembers'];holders=model['hzyholders']
    model['hzzmembers']=lambda g,p,t:membership(g,p,t) or (g,p)==('group','m2') and t in ('anchor','operation')
    model['hzyholders']=lambda p,r,i,g,t:holders(p,r,i,g,t) or (p,r,i,g,t)==('m2','memberrole','institution','group','anchor')
    model['jiremaining']=lambda actor,group,community,anchor:remaining and (actor,group,community,anchor)==('speaker','group','community','anchor')
    if variant=='different_members':
        members=model['hzzmembers']
        model['hzzmembers']=lambda g,p,t:members(g,p,t) or (g,p,t)==('group','other','anchor')
    elif variant=='different_assigned_community':
        assignment=model['hzyassigned']
        model['hzyassigned']=lambda i,g,c,code,t:assignment(i,g,'other',code,t)
    elif variant=='different_protected_community':model['hzxcommunity']=lambda *args:'protectother'
    elif variant=='different_commander':
        holds=model['hzyholders']
        model['hzyholders']=lambda p,r,i,g,t:holds('other' if p=='speaker' else p,r,i,g,t)
    elif variant.startswith('unknown_'):
        name={'unknown_mission':'hzzunitmethods','unknown_protection':'hzxmembersof',
              'unknown_remaining':'jiremaining','unknown_mapping':'qa'}[variant]
        def unknown(*args):raise ValueError('Unknown integrated input: '+name)
        model[name]=unknown
    else:assert variant=='baseline',variant
    required={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    assert not required-set(model),required-set(model)
    return doc,dict(individuals=individuals,situations=scenes,primitives={n:model[n] for n in required},
        memoize_definitions=True,memoize_expressions=True,max_steps=2_000_000)


def values(*,indices=(0,),short_circuit=True,memoize=True,**options):
    doc,kwargs=fixture(**options);doc['statements']=[doc['statements'][i] for i in indices]
    if short_circuit:doc,kwargs['primitives']=lower(doc,kwargs['primitives'])
    kwargs.update(memoize_definitions=memoize,memoize_expressions=memoize)
    return [row['value'] for row in evaluate_document(doc,**kwargs)]


def build_report():
    doc,kwargs=fixture()
    source=parse((ROOT/SOURCE).read_text(encoding='utf-8'))
    original={d['name']:d for d in source['declarations']}
    changed={d['name'] for d in doc['declarations'] if d['name'] in original and d!=original[d['name']]}
    expected_changes={'rtx','rvy','hzxtasks','hzxcommandcodes','hztcontextfor','hzthearersfor','hztspeakerfor'}
    assert changed==expected_changes,changed
    preserved=[d['name'] for d in doc['declarations'] if d['name'] in original and d['name'] not in changed]
    from noema.script import transcribe
    for notation in ('full','compact'):
        text=format_graph(doc,notation)
        assert parse(text)==doc and parse(transcribe(text,alphabet='v2'))==doc
    baseline=values(indices=tuple(range(7)));assert baseline==[True]*7
    omissions={name:values(**{name:False}) for name in COMPONENTS}
    assert all(result==[False] for result in omissions.values())
    contrasts={name:values(variant=name) for name in CONTRASTS}
    assert all(result==[False] for result in contrasts.values())
    assert values(success=False,remaining=False)==[True]
    unknowns={}
    for name in UNKNOWNS:
        assert values(variant=name,indices=(1,))==[True]
        try:values(variant=name)
        except ValueError as error:
            assert 'Unknown integrated input' in str(error),str(error)
            unknowns[name]=str(error)
        else:raise AssertionError('Unknown integrated input was filled')
    budgets={}
    for name,options in [('default_eager',dict(short_circuit=False)),('lowered_without_memoization',dict(memoize=False))]:
        try:values(**options)
        except ValueError as error:
            assert 'step budget' in str(error),str(error)
            budgets[name]=str(error)
        else:raise AssertionError('Recorded budget limit no longer reproduced')
    lowered,model=lower(doc,kwargs['primitives'])
    counts=Counter()
    def observed(name,fn):
        def call(*args):
            counts[name]+=1
            return fn(*args)
        return call
    kwargs['primitives']={name:observed(name,fn) for name,fn in model.items()}
    lowered['statements']=lowered['statements'][:1]
    assert [row['value'] for row in evaluate_document(lowered,**kwargs)]==[True]
    for name in ('hztavailable','ae','hzwavailable','hzzunitmethods','hzyassigned','hzxmembersof'):
        assert counts[name]>0,name
    # Pin imported local implementation modules and their named Noema inputs.
    paths={SOURCE,'tests/test_integrated_qualification.py','tests/test_diagnostic_short_circuit.py',
           'docs/integrated-qualification-v1.md', 'scripts/check_integrated_qualification.py'}
    for name,module in tuple(sys.modules.items()):
        if not name.startswith(('noema.','scripts.')):continue
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).resolve()
            if path.is_relative_to(ROOT):paths.add(path.relative_to(ROOT).as_posix())
        if name.startswith('scripts.'):
            for field in ('PARENT','SOURCE','CORE','LIBRARY','EXAMPLE'):
                path=getattr(module,field,None)
                if isinstance(path,str) and path.endswith('.noema') and (ROOT/path).is_file():paths.add(path)
    return dict(status='combined_finite_diagnostic_only',source=SOURCE,
        source_semantic_definitions_preserved=preserved,fixture_specializations=sorted(changed),
        diagnostic_graph_sha256=hashlib.sha256(format_graph(doc,'compact').encode('utf-8')).hexdigest(),
        declarations=len(doc['declarations']),individuals=list(kwargs['individuals']),situations=list(kwargs['situations']),
        baseline=baseline,component_omissions=omissions,identity_contrasts=contrasts,
        no_utterance_with_failed_residual=True,unknowns=unknowns,budget_limit=kwargs['max_steps'],budget_refusals=budgets,
        baseline_primitive_calls=dict(sorted(counts.items())),roundtrips=True,
        description_domains={'rvy':['hzvshadow','jktarget'],'rtx':['jnact','jnalias']},
        stored_description_domains_remain_unbounded=True,source_coverage_added=False,
        full_domain_proof=False,semantic_completion=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--verify-only',action='store_true')
    args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Integrated finite qualification verified; no new source coverage or completed units')


if __name__=='__main__':main()
