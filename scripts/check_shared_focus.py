"""Independent finite specifications for shared information structure."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from pathlib import Path
import hashlib
import json
from noema.constructed_semantics import evaluate_document
from scripts.shared_focus import *

PEOPLE=('a','b');TIMES=('now','later')
CONSTANTS=dict(first='a',second='b',node='a',author='b',topic='a',foregroundscope='a',backgroundscope='b',firstnode='a',secondnode='b')
STAGES=dict(context='now',anchor='now',elsewhere='later')
SIGNATURES=dict(payload=function_sort([I,S],T),comparisons=WINDOW,ranking=RANKING,reported=REPORT,backgrounded=BACKGROUND,about=ABOUT,
    records=REPORT,contrasts=function_sort([I,I,TC,TC,I,S],T),before=function_sort([I,I,S],T),expects=EXPECTS)
ACTION=description_sort(function_sort([I,I],C))
EXAMPLES={n:'examples/v016/focus-'+n+'-v1.noema' for n in ('exclusion','addition','scalar','topiccontrast')}

def claim(n='focusform'):return quote(call(n),1)
def descriptions(names=('alternativeform',)):return dict(kind='sequence',element=PC,items=[claim(n) for n in names])
def wrapped(x):return quote(x,1)
def unknown(*a):raise ValueError('Unknown focus interpretation')
def subsets(items):return [{x for i,x in enumerate(items) if mask&(1<<i)} for mask in range(1<<len(items))]
def code_name(description):
    node=json.loads(description.syntax)
    return node['symbol'] if node['kind']=='call' else json.dumps(node,sort_keys=True)
def ev(content,point=None):return dict(kind='evaluate',content=content,situation=call('context') if point is None else point)
def package(name='focusalso',names=('alternativeform',)):
    return call(name,wrapped(claim()),wrapped(descriptions(names)),quote(ref('comparisons')))
def scalar(name='focusscalaralso',names=('alternativeform',)):
    return call(name,wrapped(claim()),wrapped(descriptions(names)),quote(call('author')),quote(call('anchor')),quote(ref('ranking')))
def topical():return call('focuspackage',call('topiccontent',quote(ref('topicframe'),2),quote(call('first'))),quote(call('weakform'),2))
def contrast():return call('contrastpackage',wrapped(claim('weakform')),wrapped(claim()),quote(call('author')),quote(call('anchor')),quote(ref('expects')))

@lru_cache(maxsize=1)
def base():
    d=deepcopy(composed())
    d['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=I) for n in CONSTANTS]
    d['declarations'] += [dict(kind='primitive',name=n,parameters=[],result=S) for n in STAGES]
    d['declarations'] += [dict(kind='primitive',name=n,parameters=t['parameters'],result=t['result']) for n,t in SIGNATURES.items()]
    for name,item in [('focusform','first'),('focusalias','first'),('alternativeform','second')]:
        d['declarations'].append(definition(name,[],C,content(call('payload',call(item),v('world')))))
    d['declarations'] += [definition('weakform',[],C,content(truth(True))),definition('falseform',[],C,content(truth(False))),
        definition('topicframe',[('item',I)],C,content(op('implies',eq(v('item'),call('first')),op('not',call('payload',call('first'),v('world')))))),
        definition('otherframe',[('item',I)],C,content(op('implies',eq(v('item'),call('first')),op('not',call('payload',call('first'),v('world'))))))]
    for name,item in [('actionfirst','first'),('actionsecond','second')]:
        d['declarations'].append(definition(name,[('person',I),('activity',I)],C,content(call('payload',call(item),v('world')))))
    d['declarations'].append(definition('actionframe',[('action',ACTION)],C,
        dict(kind='apply',function=disquote(v('action')),arguments=[call('first'),call('second')])))
    return normalize_document(d)

def doc(bodies):
    d=deepcopy(base());d['statements']=[dict(kind='ask',body=b) for b in bodies];return normalize_document(d)
def query(name,**overrides):
    declaration=next(d for d in raw()['declarations'] if d['name']==name)
    roles=OLD_ROLES.get(name,[p['name'] for p in declaration['parameters']])
    replacements=dict(package=topical(),reference=quote(call('first')),frame=quote(ref('topicframe'),2),
        foreground=call('focusthirdrank',call('focusclaim',topical())),background=call('focusthirdrank',call('focusbackground',topical())),
        first=call('firstnode'),second=call('secondnode'),left=quote(call('weakform'),3),right=quote(call('focusform'),3),scope=call('foregroundscope'))
    replacements.update(overrides)
    return call(name,*[replacements.get(n,ref(n) if isinstance(p['sort'],dict) and p['sort']['kind']=='function' else call(n))
        for n,p in zip(roles,declaration['parameters'])])
def model(**overrides):
    m={d['name']:unknown for d in base()['declarations'] if d['kind']=='primitive'}
    m.update({n:(lambda x=x:x) for n,x in (CONSTANTS|STAGES).items()})
    m.update(payload=lambda i,w:i=='a' and w=='now',comparisons=lambda w:True,
        ranking=lambda o,a,b,s:o=='b' and code_name(a)=='focusform' and code_name(b)=='alternativeform' and s=='now',
        reported=lambda *a:True,backgrounded=lambda *a:True,about=lambda *a:True,records=lambda *a:True,contrasts=lambda *a:True,
        before=lambda a,b,s:(a,b,s)==('a','b','now'),expects=lambda o,a,b,s,w:o=='b' and s=='now' and w=='later')
    m.update(overrides);return m
def values(d,m,scenes=TIMES):return [r['value'] for r in evaluate_document(d,individuals=PEOPLE,situations=scenes,primitives=m,max_steps=2000000)]

@lru_cache(maxsize=1)
def alternative_checks():
    bodies=[call('focusentails',claim(),claim('alternativeform'),ref('comparisons')),
        call('focusequivalent',claim(),claim('alternativeform'),ref('comparisons')),
        ev(call('focusexclusion',claim(),descriptions(),ref('comparisons'))),ev(call('focusaddition',claim(),descriptions(),ref('comparisons')))]
    for name in ('focusonly','focusalso'):
        bodies += [call(n,package(name),call('context')) for n in ('focusclaimtrue','focusbackgroundtrue')]
    d=doc(bodies);count=0
    for focus,other,scope,point in product(subsets(TIMES),subsets(TIMES),subsets(TIMES),TIMES):
        entails=(focus&scope)<=other;equivalent=focus&scope==other&scope
        excluded=point in scope and (entails or point not in other)
        added=point in scope and not entails and point in other
        expected=[entails,equivalent,excluded,added,excluded,point in focus,point in focus,added]
        m=model(payload=lambda i,w:w in (focus if i=='a' else other),comparisons=lambda w:w in scope,context=lambda:point)
        if values(d,m)!=expected:raise ValueError('Alternative specification differs')
        count+=1
    return dict(models=count,situations=2,checks_per_model=8)

def direct_pair(left,right):return call('focuspackage',quote(call(left),2),quote(call(right),2))
@lru_cache(maxsize=1)
def projection_checks():
    d=deepcopy(base())
    for name in ('firstbackground','secondbackground'):
        d['declarations'].append(dict(kind='primitive',name=name,parameters=[S],result=T))
        d['declarations'].append(definition(name+'form',[],C,content(call(name,v('world')))))
    left=direct_pair('focusform','firstbackgroundform');right=direct_pair('alternativeform','secondbackgroundform')
    packages=[call('focusnegate',left)]+[call(n,left,right) for n in ('focusand','focusif','focusfilteredif')]
    d['statements']=[dict(kind='ask',body=call(n,p,call('context'))) for p in packages for n in ('focusclaimtrue','focusbackgroundtrue')]
    d=normalize_document(d);count=0
    for p,q,r,s in product((False,True),repeat=4):
        expected=[not p,r,p and q,r and s,(not p or q),r and s,(not p or q),r and (not p or s)]
        if values(d,model(payload=lambda i,w:p if i=='a' else q,firstbackground=lambda w:r,secondbackground=lambda w:s))!=expected:
            raise ValueError('Background projection differs')
        count+=1
    return dict(models=count,independent_truths=4,checks_per_model=8)

@lru_cache(maxsize=1)
def scalar_checks():
    count=0;edges=list(product(('focusform','alternativeform'),repeat=2))
    for names in ((),('alternativeform',),('focusform',),('alternativeform','alternativeform')):
        sequence=descriptions(names);items=['focusform',*names]
        bodies=[call('focusorder',descriptions(items),call('author'),call('anchor'),ref('ranking')),
            call('focusextreme',claim(),sequence,call('author'),call('anchor'),ref('ranking')),
            call('focusadditional',sequence,call('context'))]
        bodies += [call(n,scalar(p,names),call('context')) for p in ('focusscalar','focusscalaralso') for n in ('focusclaimtrue','focusbackgroundtrue')]
        d=doc(bodies)
        for relation,p,r in product(subsets(edges),(False,True),(False,True)):
            ordered=all((x,x) not in relation for x in items) and all((a,c) in relation for a,b,c in product(items,repeat=3) if (a,b) in relation and (b,c) in relation)
            extreme=bool(names) and ordered and all(n!='focusform' and ('focusform',n) in relation for n in names)
            extra=any(p if n=='focusform' else r for n in names)
            m=model(payload=lambda i,w:p if i=='a' else r,ranking=lambda o,a,b,s:(code_name(a),code_name(b)) in relation)
            if values(d,m)!=[ordered,extreme,extra,p,extreme,p,extreme and extra]:raise ValueError('Scalar specification differs')
            count+=1
    return dict(models=count,description_names=2,alternative_lists=4,checks_per_model=7)

@lru_cache(maxsize=1)
def contrast_checks():
    pack=call('contrastpackage',wrapped(claim()),wrapped(claim('alternativeform')),quote(call('author')),quote(call('anchor')),quote(ref('expects')))
    d=doc([call(n,p,call('context')) for p in (pack,call('focusnegate',pack)) for n in ('focusclaimtrue','focusbackgroundtrue')]);count=0
    for left,right,candidates,point in product(subsets(TIMES),subsets(TIMES),subsets(TIMES),TIMES):
        foreground=point in left and point in right;background=bool(candidates) and candidates<=left and not candidates&right
        m=model(payload=lambda i,w:w in (left if i=='a' else right),expects=lambda o,l,r,s,w:w in candidates,context=lambda:point)
        if values(d,m)!=[foreground,background,not foreground,background]:raise ValueError('Expectation contrast differs')
        count+=1
    return dict(models=count,situations=2,checks_per_model=4)

@lru_cache(maxsize=1)
def binding_diagnostics():
    fg=call('focusthirdrank',call('focusclaim',topical()));bg=call('focusthirdrank',call('focusbackground',topical()))
    left=quote(call('weakform'),3);right=quote(call('focusform'),3)
    tuples=dict(reported=[[call('node'),call('author'),fg,call('foregroundscope'),call('context')]],
        backgrounded=[[call('node'),call('author'),fg,bg,call('foregroundscope'),call('backgroundscope'),call('context')]],
        about=[[call('node'),call('author'),quote(call('first')),call('focusclaim',topical()),call('context')]],
        records=[[call('firstnode'),call('author'),left,call('foregroundscope'),call('context')],
            [call('secondnode'),call('author'),right,call('foregroundscope'),call('context')]],
        contrasts=[[call('node'),call('author'),left,right,call('foregroundscope'),call('context')]],
        before=[[call('firstnode'),call('secondnode'),call('context')]],
        expects=[[call('author'),claim('weakform'),claim(),call('anchor'),call('elsewhere')]],
        ranking=[[call('author'),claim(),claim('alternativeform'),call('anchor')]])
    def describe(x):return (x.rank,x.syntax) if hasattr(x,'syntax') else x
    def arguments(expressions,sorts):
        captured=[];d=deepcopy(base())
        d['declarations'].append(dict(kind='primitive',name='capture',parameters=sorts,result=T))
        d['statements']=[dict(kind='ask',body=call('capture',*expressions))]
        m=model(capture=lambda *xs:captured.extend(xs) or True)
        if values(normalize_document(d),m)!=[True]:raise ValueError('Argument capture failed')
        return [describe(x) for x in captured]
    rows=[]
    for relation,expressions in tuples.items():
        body=query('topicmarked') if relation in ('reported','backgrounded','about') else (
            call('focusbackgroundtrue',contrast(),call('context')) if relation=='expects' else
            call('focusbackgroundtrue',scalar('focusscalar'),call('context')) if relation=='ranking' else query('contrastordered'))
        d=doc([body]);wanted=[tuple(arguments(xs,SIGNATURES[relation]['parameters'])) for xs in expressions]
        interpretation=lambda options:lambda *xs:tuple(describe(x) for x in xs) in options
        if values(d,model(**{relation:interpretation(wanted)}))!=[True]:raise ValueError('Original focus binding fails: '+relation)
        for row_index,row in enumerate(wanted):
            for slot,(value,sort) in enumerate(zip(row,SIGNATURES[relation]['parameters'])):
                if sort==I:other='b' if value=='a' else 'a'
                elif sort==S:other='later' if value=='now' else 'now'
                else:
                    expr=quote(call('second')) if sort['result']==I else quote(call('falseform'),sort.get('rank',0))
                    other=arguments([expr],[sort])[0]
                changed=[list(xs) for xs in wanted];changed[row_index][slot]=other;changed=[tuple(xs) for xs in changed]
                if values(d,model(**{relation:interpretation(changed)}))!=[False]:raise ValueError('Misbound focus tuple accepted: '+relation)
                rows.append(dict(relation=relation,tuple=row_index,slot=slot,result=False))
    return rows

def example(mode):
    if mode not in EXAMPLES:raise ValueError('Unknown focus example')
    d=deepcopy(base());ds=[x for x in d['declarations'] if x['name'] not in SIGNATURES]
    cut=next(i for i,x in enumerate(ds) if x['name']=='focusform')
    payload=op('or',op('and',eq(v('item'),call('first')),op('or',eq(v('world'),call('context')),eq(v('world'),call('laterpoint')))),
        op('and',eq(v('item'),call('second')),op('or',eq(v('world'),call('otherpoint')),eq(v('world'),call('context')) if mode=='addition' else truth(False))))
    intro=[dict(kind='primitive',name=n,parameters=[],result=S) for n in ('laterpoint','otherpoint')]
    intro += [definition('payload',[('item',I),('world',S)],T,payload),definition('comparisons',[('point',S)],T,truth(True)),
        definition('ranking',[('observer',I),('left',PC),('right',PC),('anchor',S)],T,
            allof(eq(v('observer'),call('author')),eq(v('left'),claim()),eq(v('right'),claim('alternativeform')),eq(v('anchor'),call('anchor'))))]
    # Ranking refers to content definitions, so insert it after those bodies.
    ranking=intro.pop();ds=ds[:cut]+intro+ds[cut:];ds.append(ranking)
    def match(name,targets):
        sort=SIGNATURES[name];ps=[('arg'+chr(97+i),t) for i,t in enumerate(sort['parameters'])]
        return definition(name,ps,T,allof(*(eq(v(n),x) for (n,t),x in zip(ps,targets))))
    fg=call('focusthirdrank',call('focusclaim',topical()));bg=call('focusthirdrank',call('focusbackground',topical()))
    ds += [match('reported',[call('node'),call('author'),fg,call('foregroundscope'),call('context')]),
        match('backgrounded',[call('node'),call('author'),fg,bg,call('foregroundscope'),call('backgroundscope'),call('context')]),
        match('about',[call('node'),call('author'),quote(call('first')),call('focusclaim',topical()),call('context')]),
        match('before',[call('firstnode'),call('secondnode'),call('context')]),
        match('expects',[call('author'),claim('weakform'),claim(),call('anchor'),call('otherpoint')])]
    left=quote(call('weakform'),3);right=quote(call('focusform'),3)
    one=match('records',[call('firstnode'),call('author'),left,call('foregroundscope'),call('context')])
    two=match('records',[call('secondnode'),call('author'),right,call('foregroundscope'),call('context')])
    one['body']=op('or',one['body'],two['body']);ds.append(one)
    ds.append(match('contrasts',[call('node'),call('author'),left,right,call('foregroundscope'),call('context')]))
    selected=package('focusonly' if mode=='exclusion' else 'focusalso') if mode in ('exclusion','addition') else scalar() if mode=='scalar' else topical()
    bodies=[call(n,p,call('context')) for p in (selected,call('focusnegate',selected)) for n in ('focusclaimtrue','focusbackgroundtrue')]
    bodies += [query('topicmarked'),query('focusattributepackage'),query('contrastordered')]
    bodies += [call(n,contrast(),call('context')) for n in ('focusclaimtrue','focusbackgroundtrue')]
    bodies += [eq(call('focusbackground',selected),call('focusbackground',call('focusnegate',selected))),
        query('topicmarked',topic=call('second')),query('topicmarked',frame=quote(ref('otherframe'),2))]
    # Both action descriptions are applied to exactly the same frame.
    framed=quote(ref('actionframe'),1)
    actions=dict(kind='sequence',element=ACTION,items=[quote(ref('actionsecond')),quote(ref('actionfirst'))])
    bodies += [eq(call('focusactions',framed,actions),dict(kind='sequence',element=PC,
        items=[call('focusaction',framed,quote(ref(n))) for n in ('actionsecond','actionfirst')])),
        eq(disquote(call('focusquotedlist',descriptions())),descriptions())]
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=[dict(kind='ask',body=b) for b in bodies]))

EXAMPLE_SCENES=('now','later','other')
def example_model():return {n:(lambda x=x:x) for n,x in (CONSTANTS|STAGES|dict(laterpoint='later',otherpoint='other')).items()}
def example_expected(mode):
    foreground=mode!='topiccontrast';background=mode!='scalar'
    return [foreground,background,not foreground,background,True,True,True,True,True,True,False,False,True,True]

def prepare():
    from scripts.shared_focus import prepare as prepare_library
    prepare_library()
    for mode,path in EXAMPLES.items():
        target=ROOT/path;text=format_graph(example(mode))+'\n'
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published focus example differs')
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')

def build_report():
    from noema.meaning_catalog import load_catalog
    if load_catalog(ROOT,BASIS).document!=composed() or json.loads((ROOT/BASIS).read_text(encoding='utf-8'))!=basis():raise ValueError('Focus basis differs')
    examples={}
    for mode,path in EXAMPLES.items():
        d=example(mode)
        if parse((ROOT/path).read_text(encoding='utf-8'))!=d:raise ValueError('Focus example differs')
        actual=values(d,example_model(),EXAMPLE_SCENES)
        if actual!=example_expected(mode):raise ValueError('Integrated focus meaning differs: '+mode)
        examples[mode]=actual
    result=dict(schema='noema-shared-focus-report-1',definitions=38,preserved_definitions=22,new_definitions=16,new_primitive_declarations=0,
        alternatives=alternative_checks(),projection=projection_checks(),scalar=scalar_checks(),contrast=contrast_checks(),
        single_slot_binding_diagnostics=binding_diagnostics(),examples=examples)
    paths=[LIBRARY,BASIS,*EXAMPLES.values(),'scripts/shared_focus.py','scripts/check_shared_focus.py','tests/test_shared_focus.py','docs/shared-focus-v1.md',*basis()['design_sources']]
    for source in SOURCES:paths.extend((source['document'],source['basis']))
    for name in ('scalar-backgrounds','focused-permission','ordered-contrast','attributed-focus','count-focus'):
        report='reports/'+name+'-v1.json';hashes=json.loads((ROOT/report).read_text(encoding='utf-8'))['source_sha256'];paths.extend((report,*hashes))
        for path,digest in hashes.items():
            if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:raise ValueError('Earlier focus evidence changed: '+path)
    import sys
    for name,module in tuple(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if name.startswith('noema.') and path and ROOT in Path(path).resolve().parents:paths.append(Path(path).resolve().relative_to(ROOT).as_posix())
    result['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(paths))}
    result['limits']=LIMITS;return result
