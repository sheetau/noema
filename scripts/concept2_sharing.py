"""Scope-local sharing of values, open expressions and costly bound references.

An expanded native tree must be exact. Candidate allocation is deterministic;
the accepted v7 planner remains a costed alternative, not a random style switch.
"""
from collections import Counter
from copy import deepcopy
from scripts.concept2_composition import key,simple_word,expand_plan,spelling_units,bounds,alias_shape,M
from scripts import concept2_composition as previous,concept2_geometry_v5 as g


def candidate_plan(statement,dictionary,*,sharing=True):
    """Conservative local CSE: quotes/binders establish distinct namespaces."""
    spellings=dictionary['selected_spellings'];decl={d['name']:d for d in dictionary['native']['declarations']}
    statistics=Counter()
    def region(root,dot_counter=None,binders=()):
        if dot_counter is None:dot_counter=[0]
        occurrences=[]
        def scan(v):
            if isinstance(v,dict):
                if 'kind' in v:occurrences.append(v)
                if v.get('kind') in ('quote','lambda','forall','exists','content'):return
                for x in v.values():scan(x)
            elif isinstance(v,list):
                for x in v:scan(x)
        scan(root);freq=Counter(key(v) for v in occurrences)
        unique={key(v):v for v in occurrences};first={}
        for i,v in enumerate(occurrences):first.setdefault(key(v),i)
        def cost(value):
            if isinstance(value,list):return sum(cost(v) for v in value)
            if not isinstance(value,dict):return 0
            if value.get('kind')=='variable':
                depth=binders[::-1].index(value['name']) if value['name'] in binders else 0
                return 1+2*(depth//5)+min(depth%5,2)
            return (len(spellings[value['symbol']]) if 'symbol' in value else int('kind' in value))+sum(cost(v) for v in value.values())
        costs={k:cost(v) for k,v in unique.items()}
        slots={};used_lanes=set()
        if sharing:
            candidates=[k for k,v in unique.items() if freq[k]>=3 and (simple_word(v) or costs[k]>=3) and v.get('kind') not in ('assert','ask','perform','suppose','lambda','forall','exists','content')]
            candidates.sort(key=lambda k:(-((freq[k]-1)*costs[k]),first[k]))
            for k in candidates:
                v=unique[k];word=simple_word(v)
                sort=decl[v['symbol']]['result'] if v.get('kind')=='call' else 'description' if v.get('kind')=='quote' else None
                preferred=1 if sort=='situation' else -1 if sort=='individual' else 0
                lanes=[preferred]+[x for x in (-1,1,0) if x!=preferred]
                lane=next((x for x in lanes if x not in used_lanes),None)
                if lane is None:break
                slots[k]=lane;used_lanes.add(lane)
        modes=Counter((w[1],w[2]) for v in occurrences if (w:=simple_word(v)) and w[1].startswith('quoted_'))
        templates={}
        if sharing:
            for mode,n in modes.most_common():
                if n<2:continue
                lane=next((x for x in (0,-1,1) if x not in used_lanes),None)
                if lane is None:break
                templates[mode]=lane;used_lanes.add(lane)
        dots={};locals_={}
        if sharing:
            candidates=[k for k,v in unique.items() if k not in slots and freq[k]>=2 and first[k]>0
                        and costs[k]>=5
                        and v.get('kind') not in ('lambda','forall','exists','content')]
            candidates.sort(key=lambda k:(-costs[k],first[k]))
            for k in candidates:
                positions=[i for i,v in enumerate(occurrences) if key(v)==k]
                if freq[k]==2 and positions[-1]-positions[0]>=6 and dot_counter[0]<256 and len(locals_)>=8:
                    dots[k]=dot_counter[0];dot_counter[0]+=1
                elif len(locals_)<8:locals_[k]=len(locals_)
        symbol_counts=Counter(v['symbol'] for v in occurrences if v.get('kind') in ('call','function_ref'))
        repeated_words=[s for s,n in symbol_counts.items() if sharing and n>=2 and len(spellings[s])>=3]
        word_names={s:i for i,s in enumerate(repeated_words[:8])}
        # Declared locally, never a global word-number assignment. The visible
        # definition carries the actual spelling, and the name has no meaning
        # outside this region.
        seen_roles=set();seen_templates=set();seen_dots=set();seen_locals=set();seen_words=set()
        def convert(v,*,allow_binding=True):
            if isinstance(v,list):return [convert(x) for x in v]
            if not isinstance(v,dict):return deepcopy(v)
            k=key(v)
            if allow_binding and k in slots:
                lane=slots[k]
                if k in seen_roles:statistics['role-use']+=1;return dict(form='role-use',lane=lane)
                seen_roles.add(k);statistics['role-definition']+=1
                return dict(form='role-definition',lane=lane,value=convert(v,allow_binding=False))
            if allow_binding and k in dots:
                label=dots[k]
                if k in seen_dots:statistics['dot-use']+=1;return dict(form='dot-use',label=label)
                seen_dots.add(k);statistics['dot-definition']+=1
                return dict(form='dot-definition',label=label,value=convert(v,allow_binding=False))
            if allow_binding and k in locals_:
                label=locals_[k]
                if k in seen_locals:statistics['local-use']+=1;return dict(form='local-use',label=label)
                seen_locals.add(k);statistics['local-definition']+=1
                return dict(form='local-definition',label=label,value=convert(v,allow_binding=False))
            word=simple_word(v)
            if word and (word[1],word[2]) in templates:
                mode=(word[1],word[2]);lane=templates[mode]
                payload=dict(kind='function_ref',symbol=word[0]) if word[1]=='quoted_ref' else dict(kind='call',symbol=word[0],arguments=[])
                if mode not in seen_templates:
                    seen_templates.add(mode);statistics['template-definition']+=1
                    return dict(form='template-definition',lane=lane,mode=word[1],rank=word[2],value=convert(payload,allow_binding=False))
                statistics['template-use']+=1
                return dict(form='template-use',lane=lane,value=convert(payload,allow_binding=False))
            if v.get('kind') in ('quote','lambda','forall','exists','content'):
                isolated=v['kind']=='quote'
                inner=() if isolated else (*binders,*([p['name'] for p in v['parameters']] if v['kind']=='lambda' else [v['variable']]))
                result=deepcopy(v);result['body']=dict(form='scope',quotation=isolated,body=region(v['body'],None if isolated else dot_counter,inner))
                statistics['scope']+=1;return result
            result={}
            if v.get('kind') in ('call','function_ref'):
                symbol=v['symbol']
                if symbol in word_names:
                    label=word_names[symbol]
                    if symbol not in seen_words:
                        seen_words.add(symbol);statistics['word-definition']+=1
                        symbol_plan=dict(form='word-definition',label=label,parts=spellings[symbol])
                    else:
                        statistics['word-use']+=1;symbol_plan=dict(form='word-use',label=label)
                else:symbol_plan=dict(form='word',parts=spellings[symbol])
            for a,b in v.items():result[a]=symbol_plan if a=='symbol' else convert(b)
            return result
        result=convert(root)
        # A shared outer expression can hide the only later use of an inner
        # candidate. Remove unused bindings before checking paired dots.
        live=Counter()
        def collect(v):
            if isinstance(v,list):
                for x in v:collect(x)
            elif isinstance(v,dict):
                if v.get('form')=='scope':return
                if v.get('form') in ('role-use','local-use','dot-use'):
                    live[(v['form'].split('-')[0],v.get('lane',v.get('label')))]+=1
                for x in v.values():collect(x)
        collect(result)
        def remove_unused(v):
            if isinstance(v,list):return [remove_unused(x) for x in v]
            if not isinstance(v,dict) or v.get('form')=='scope':return v
            f=v.get('form','')
            if f in ('role-definition','local-definition','dot-definition') and not live[(f.split('-')[0],v.get('lane',v.get('label')))]:
                return remove_unused(v['value'])
            return {k:remove_unused(x) for k,x in v.items()}
        result=remove_unused(result)
        definitions={};uses=Counter()
        def inventory(v):
            if isinstance(v,list):
                for x in v:inventory(x)
            elif isinstance(v,dict):
                if v.get('form')=='scope':return
                if v.get('form')=='word-definition':definitions[v['label']]=v['parts']
                if v.get('form')=='word-use':uses[v['label']]+=1
                for x in v.values():inventory(x)
        inventory(result);remove=set()
        for label,parts in definitions.items():
            forms=spelling_units(parts)
            width=sum(bounds(x['shapes'])[2]-bounds(x['shapes'])[0] for x in forms)+M*(len(forms)-1)
            call_width=bounds(alias_shape(label,word=True))[2]-bounds(alias_shape(label,word=True))[0]
            declaration_width=call_width+M
            if uses[label]*(width-call_width)<=declaration_width:remove.add(label)
        def prune(v):
            if isinstance(v,list):return [prune(x) for x in v]
            if not isinstance(v,dict):return v
            if v.get('form')=='scope':return v
            if v.get('form') in ('word-definition','word-use') and v['label'] in remove:
                return dict(form='word',parts=definitions[v['label']])
            return {k:prune(x) for k,x in v.items()}
        return prune(result)
    plan=dict(form='scope',quotation=True,body=region(statement))
    assert expand_plan(plan,dictionary)==statement
    final=Counter()
    def count(v):
        if isinstance(v,list):
            for x in v:count(x)
        elif isinstance(v,dict):
            if v.get('form') not in (None,'word'):final[v['form']]+=1
            for x in v.values():count(x)
    count(plan)
    return dict(plan=plan,features=dict(final))


def token_width(tokens,codec):
    # A cheap deterministic first gate. Final layouts are measured at publication.
    return sum(g.bounds(codec.forms[t]['shapes'])[2]-g.bounds(codec.forms[t]['shapes'])[0]+g.M for t in tokens)


def choose_plan(source,codec,*,expression=False):
    if source.get('kind')=='suppose':
        condition=choose_plan(dict(kind='assert',body=source['condition']),codec)['plan']
        condition['body']=condition['body']['body']
        children=[choose_plan(s,codec) for s in source['statements']]
        plan=dict(kind='suppose',condition=condition,statements=[c['plan'] for c in children])
        assert expand_plan(plan,codec.dictionary)==source
        return dict(plan=plan,policy='separate-statement-scopes')
    old=previous.make_plan(source,codec.dictionary)
    new=candidate_plan(source,codec.dictionary)
    before=codec.encode(old['plan'],expression=expression)
    after=codec.encode(new['plan'],expression=expression)
    old_width=token_width(before,codec);new_width=token_width(after,codec)
    selected=new if new_width<old_width-1e-5 else old
    return dict(selected,policy='scope-local' if selected is new else 'v7',
        previous_tokens=len(before),candidate_tokens=len(after),previous_width=old_width,candidate_width=new_width)
