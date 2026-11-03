"""Recover an asymmetric main flow and terminal dependencies from visible ink.

Circle-pair contraction is explicit here. The recovered nodes are not yet words.
The caller supplies observed geometry, never source paths or emitted groups.
"""
from collections import defaultdict
import math
from scripts.kant_geometry_reader import recover_seams


def decompose_flow(geometry, *, terminal_words=False):
    circles=geometry['circles'];parents=list(range(len(circles)))
    def root(i):
        while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
        return i
    for relation in geometry['relations']:
        if relation['kind']!='tangent':
            a,b=relation['circles'];parents[root(a)]=root(b)
    members=defaultdict(list)
    for i in range(len(circles)):members[root(i)].append(i)
    sizes={'small':0,'medium':1,'large':2}
    clusters=sorted(members.values(),key=lambda ids:min(tuple(circles[i]['center']) for i in ids))
    owner={c:i for i,ids in enumerate(clusters) for c in ids}
    nuclei=[]
    for ids in clusters:
        main=max(ids,key=lambda i:sizes[circles[i]['size']])
        nuclei.append(dict(circles=ids,center=circles[main]['center'],size=circles[main]['size']))
    adjacency={i:set() for i in range(len(nuclei))}
    def link(a,b):
        if a!=b:adjacency.setdefault(a,set()).add(b);adjacency.setdefault(b,set()).add(a)
    vertices=[]
    for i,v in enumerate(geometry['vertices']):
        owners={owner[c] for c in v['centers']+v['rims']}
        if len(owners)==1:vertices.append(next(iter(owners)))
        else:
            node=len(nuclei)+i;vertices.append(node);adjacency.setdefault(node,set())
            for other in owners:link(node,other)
    for a,b in geometry['edges']:link(vertices[a],vertices[b])
    for relation in geometry['relations']:
        if relation['kind']=='tangent':link(*(owner[c] for c in relation['circles']))
    for a,b in recover_seams(geometry):
        ends=[]
        for center in (a,b):
            owners={owner[i] for i,c in enumerate(circles) if math.dist(c['center'],center)<1e-6}
            if len(owners)!=1:raise ValueError('Ambiguous silent seam nucleus')
            ends.append(next(iter(owners)))
        link(*ends)
    # Free terminal strokes remain observable in the geometry; they are marks,
    # not terminal argument circles. Remove only their line-only graph tails.
    changed=True
    while changed:
        changed=False
        for node in list(adjacency):
            if node<len(nuclei) or len(adjacency[node])>2:continue
            neighbors=list(adjacency.pop(node))
            for other in neighbors:adjacency[other].remove(node)
            if len(neighbors)==2:link(*neighbors)
            changed=True
    if not nuclei:raise ValueError('Missing main flow')
    edge_count=sum(map(len,adjacency.values()))//2
    if edge_count!=len(adjacency)-1:raise ValueError('Nucleus flow is not one tree')
    left=min(n['center'][0] for n in nuclei)
    candidates=[i for i,n in enumerate(nuclei) if abs(n['center'][0]-left)<1e-6]
    highest=max(len(adjacency[i]) for i in candidates)
    candidates=[i for i in candidates if len(adjacency[i])==highest]
    if len(candidates)!=1:raise ValueError('Ambiguous initial nucleus')
    start=candidates[0];seen=set()
    def descendants(node,parent):
        if node in seen:raise ValueError('Cycle in nucleus flow')
        seen.add(node);result=[]
        if node<len(nuclei):result.append(node)
        for other in adjacency[node]-{parent}:result+=descendants(other,node)
        return result
    below={}
    def orient(node,parent):
        children=[]
        for other in adjacency[node]-{parent}:
            descendants_=orient(other,node);below[(node,other)]=descendants_
            children+=descendants_
        return ([node] if node<len(nuclei) else [])+children
    descendants(start,None)
    if len(seen)!=len(adjacency):raise ValueError('Disconnected nucleus flow')
    orient(start,None)
    main=[];side=[];current=start;parent=None
    while True:
        if current<len(nuclei):main.append(current);side.append([])
        children=list(adjacency[current]-{parent})
        if not children:break
        reach=lambda c:max(nuclei[i]['center'][0] for i in below[(current,c)])
        farthest=max(reach(c) for c in children)
        onward=[c for c in children if abs(reach(c)-farthest)<1e-6]
        if len(onward)!=1:raise ValueError('Ambiguous continuation at a branch')
        for child in children:
            if child==onward[0]:continue
            ids=below[(current,child)]
            if not main:raise ValueError('Nonterminal dependency outside main flow')
            if terminal_words:
                if side[-1]:raise ValueError('Multiple terminal dependencies at one nucleus')
                chain=[];previous=current;node=child
                while True:
                    if node<len(nuclei):
                        if nuclei[node]['size']=='large':
                            raise ValueError('Large nucleus in terminal word branch')
                        chain.append(node)
                    onward_=list(adjacency[node]-{previous})
                    if len(onward_)>1:raise ValueError('A terminal word branch cannot fork')
                    if not onward_:break
                    previous,node=node,onward_[0]
                side[-1]=chain
            else:
                if len(ids)!=1:raise ValueError('Nonterminal dependency outside main flow')
                side[-1].append(ids[0])
        parent,current=current,onward[0]
    if not terminal_words and any(len(ids)>1 for ids in side):raise ValueError('Multiple terminal dependencies at one nucleus')
    if sorted(main+[i for ids in side for i in ids])!=list(range(len(nuclei))):
        raise ValueError('Unvisited nucleus')
    return dict(nuclei=nuclei,main=main,side=side)
