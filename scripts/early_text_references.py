"""Construct the opening text locations using the retained source coordinates."""
from scripts.shared_reference import definition
from scripts.shared_modality import call


def declarations(anchors,names,vocabulary):
    """Keep frontmatter context separate and reuse inherited sentence locations."""
    number=lambda n:dict(kind='number',numerator=n,denominator=1)
    local=lambda n:call(names[n])
    public=lambda n,*args:call(vocabulary._symbols[n],*args)
    rows=[]
    for old in anchors['new_sentence_references']:
        paragraph,sentence=anchors['sentences'][old]
        rows.append(definition(names[old],[],'individual',public('sentencereference',
            local('ri'),number(paragraph),number(sentence))))
    for old,row in anchors['frontmatter'].items():
        rows.append(definition(names[old],[],'individual',public('frontmatterreference',
            local('eirg'),number(row['item']))))
    # The existing first section heading already has its own declaration.
    rows.append(definition(names['eisdz'],[],'individual',public('headingreference',local('ri'),number(1))))
    for old,(first,start,last,end) in anchors['spans'].items():
        rows.append(definition(names[old],[],'individual',public('sentencetokenspanreference',
            local('eirf'),local(first),number(start),local(last),number(end),local('ri'))))
    if len({d['name'] for d in rows})!=len(rows):raise ValueError('Opening text reference names collide')
    return rows
