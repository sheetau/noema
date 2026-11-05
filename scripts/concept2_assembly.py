from copy import deepcopy
from scripts import concept2_composition as previous


def expand_plan(plan,dictionary):
    aliases={tuple(r['parts']):r['symbol'] for r in dictionary['aliases']}
    def expand(v,state):
        if isinstance(v,list):return [expand(x,state) for x in v]
        if not isinstance(v,dict):return deepcopy(v)
        f=v.get('form')
        if f=='assembly':
            child={k:(x if k=='dots' else deepcopy(x)) for k,x in state.items()}
            lanes=set()
            for binding in v['bindings']:
                lane=binding['lane']
                if lane not in (-1,0,1) or lane in lanes:raise ValueError('Assembly needs distinct declared lanes')
                lanes.add(lane);value=expand(binding['value'],child)
                child['roles'][lane]=value;child['templates'].pop(lane,None)
            if not 2<=len(lanes)<=3:raise ValueError('Assembly needs two or three values')
            return expand(v['body'],child)
        if f=='scope':
            isolated=v.get('quotation',True)
            child=({k:{} for k in ('roles','templates','dots','locals','words')} if isolated else
                   {k:(x if k=='dots' else deepcopy(x)) for k,x in state.items()})
            result=expand(v['body'],child)
            if isolated:assert all(x['used'] for x in child['dots'].values()),'Unpaired dot'
            return result
        if f=='word':return aliases[tuple(v['parts'])]
        if f in ('role-use','dot-use','local-use','word-use'):
            collection={'role-use':'roles','dot-use':'dots','local-use':'locals','word-use':'words'}[f]
            label=v['lane'] if f=='role-use' else v['label']
            value=state[collection][label]
            if f=='dot-use':assert not value['used'];value['used']=True;value=value['value']
            return deepcopy(value)
        if f in ('role-definition','dot-definition','local-definition','word-definition'):
            collection={'role-definition':'roles','dot-definition':'dots','local-definition':'locals','word-definition':'words'}[f]
            label=v['lane'] if f=='role-definition' else v['label']
            value=aliases[tuple(v['parts'])] if f=='word-definition' else expand(v['value'],state)
            if f=='dot-definition' and label in state['dots']:
                assert state['dots'][label]['used'],'Previous dot is still unpaired'
            if f=='role-definition':state['templates'].pop(label,None)
            state[collection][label]=dict(value=value,used=False) if f=='dot-definition' else deepcopy(value)
            return value
        if f in ('template-definition','template-use'):
            lane=v['lane']
            body=expand(v['value'],state)
            if f=='template-definition':
                state['templates'][lane]=(v['mode'],v['rank']);state['roles'].pop(lane,None)
            mode,rank=state['templates'][lane]
            assert body['kind']==('function_ref' if mode=='quoted_ref' else 'call')
            result=dict(kind='quote',body=body)
            if rank is not None:result['rank']=rank
            return result
        if f:raise ValueError('Unknown composition form '+f)
        return {k:expand(x,state) for k,x in v.items()}
    return expand(plan,{})


def assemble_call(source,dictionary,*,lanes=None):
    """Factor one call's arbitrary argument values without changing native AST.

    Header values retain original argument order (also canonical binder order).
    Lane labels may differ from argument order; the trunk records that order.
    """
    if source.get('kind')!='call' or len(source['arguments']) not in (2,3):
        raise ValueError('Assembly expects a two/three-argument call')
    lanes=tuple(lanes if lanes is not None else ((-1,1) if len(source['arguments'])==2 else (-1,0,1)))
    if len(lanes)!=len(source['arguments']) or len(set(lanes))!=len(lanes) or any(x not in (-1,0,1) for x in lanes):
        raise ValueError('Assembly lanes must be distinct')
    plain=previous.make_plan(source,dictionary,sharing=False)['plan']['body']
    bindings=[dict(lane=lane,value=value) for lane,value in zip(lanes,plain['arguments'])]
    body=dict(plain,arguments=[dict(form='role-use',lane=lane) for lane in lanes])
    result=dict(form='assembly',bindings=bindings,body=body)
    wrapped=dict(form='scope',quotation=True,body=result)
    assert expand_plan(wrapped,dictionary)==source
    return result
