"""Opening locations resolve to exact source nodes across two presentation contexts."""
from functools import lru_cache
import json
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts import early_text_references as references
from scripts.frontmatter_reference_visible_profile import ROOT,FrontmatterReferenceVisibleVocabulary,FrontmatterReferences


@lru_cache(maxsize=1)
def setup():
    anchors=json.loads((ROOT/'data/early-text-anchors-v1.json').read_text(encoding='utf-8'))
    vocabulary=FrontmatterReferenceVisibleVocabulary()
    required={'ri','eirg','eirf','eisdz',*anchors['new_sentence_references'],*anchors['frontmatter'],*anchors['spans']}
    names={n:'local'+n for n in required}
    rows=references.declarations(anchors,names,vocabulary)
    doc=dict(schema_version='0.16',lexicon_version='0.16',declarations=vocabulary.imports({
        'sentencereference','frontmatterreference','headingreference','sentencetokenspanreference'}),statements=[])
    doc['declarations']+=[dict(kind='primitive',name=names[n],parameters=[],result=s)
        for n,s in [('ri','situation'),('eirg','situation'),('eirf','individual')]]
    doc['declarations']+=rows
    return anchors,vocabulary,names,normalize_document(doc)


def test_exact_locations_contexts_and_cross_sentence_spans():
    anchors,v,names,doc=setup();observed=[]
    front=FrontmatterReferences({('front',1):'title'})
    def sentence(context,paragraph,index):
        assert context=='body'
        return ('sentence',int(paragraph),int(index))
    def heading(context,index):
        assert context=='body' and index==1
        return 'firstpart'
    def span(document,first,start,last,end,context):
        assert document=='paper' and context=='body'
        return ('span',first,int(start),last,int(end))
    expected={n:('sentence',*anchors['sentences'][n]) for n in anchors['new_sentence_references']}
    expected.update(eisbc='title',eisdz='firstpart')
    for old,(first,start,last,end) in anchors['spans'].items():
        expected[old]=('span',expected[first],start,expected[last],end)
    handlers={v._symbols['sentencereference']:sentence,v._symbols['frontmatterreference']:front.reference,
        v._symbols['headingreference']:heading,v._symbols['sentencetokenspanreference']:span,
        names['ri']:lambda:'body',names['eirg']:lambda:'front',names['eirf']:lambda:'paper'}
    for old,wanted in expected.items():
        probe=dict(kind='primitive',name='probe',parameters=['individual'],result='truth')
        source=doc|dict(declarations=doc['declarations']+[probe],statements=[dict(kind='ask',body=
            dict(kind='call',symbol='probe',arguments=[dict(kind='call',symbol=names[old],arguments=[])]))])
        def check(value):observed.append(value);return value==wanted
        result=evaluate_document(source,individuals=('paper',*dict.fromkeys(expected.values())),
            situations=('front','body'),primitives=handlers|{'probe':check})
        assert result[0]['value'] is True,old
    assert len(observed)==len(expected)


def test_alias_occurrences_and_existing_declarations_are_not_redefined():
    anchors,v,names,doc=setup()
    declared={d['name'] for d in doc['declarations']}
    assert 'localeir7' not in declared and 'localeisaj' not in declared and 'localeisd2' not in declared
    assert anchors['sentences']['eir6']==[1,2]
    assert anchors['sentences']['eiscl']==[2,2]
    assert anchors['headings']['eisdz']['index']==1
    assert anchors['inherited_occurrence_aliases']=={
        'eir6':'seatexamplesentence','eiscl':'eighthoriginalprinciplename','eisdz':'firstpartheading'}
