from copy import deepcopy
import hashlib
import json

import pytest

from scripts.kant_page_public_context import semantic_spellings,discourse_context,reference_context,inputs,DISCOURSE_SPELLINGS,ROOT


def fixture():
    declaration=dict(kind='definition',name='old',parameters=[],result='individual',
                     body=dict(kind='call',symbol='book',arguments=[]))
    row=dict(parts=['book','aki'],kind='definition',parameters=[],result='individual',
             meaning_ja='既存の対象を指す定義。',declaration_sha256=hashlib.sha256(
                 json.dumps(declaration,sort_keys=True,ensure_ascii=False).encode()).hexdigest())
    specification=dict(schema='kant-semantic-spellings-2',meaning_basis='latest',entries={'old':row})
    bridge=dict(source_declarations=[declaration],mapping={'old':'public'})
    bases={'latest':dict(definitions=['irrelevant'],inherited_meaning_basis='base'),
           'base':dict(definitions={'old':row['meaning_ja']})}
    return specification,bridge,bases


def test_definition_spelling_retains_recorded_meaning_and_complete_body():
    spec,bridge,bases=fixture()
    result,paths=semantic_spellings(spec,'spellings',bridge,bases.__getitem__)
    assert result=={'public':dict(parts=['book','aki'],meaning_ja='既存の対象を指す定義。')}
    assert paths==['spellings','latest','base']
    bridge['source_declarations'][0]['body']['symbol']='different'
    with pytest.raises(ValueError,match='original declaration'):
        semantic_spellings(spec,'spellings',bridge,bases.__getitem__)


@pytest.mark.parametrize('change',['meaning','signature','kind','missing','cycle'])
def test_meaning_evidence_cannot_be_relabelled_or_skipped(change):
    spec,bridge,bases=fixture()
    if change=='meaning':spec['entries']['old']['meaning_ja']='別の意味'
    if change=='signature':spec['entries']['old']['result']='truth'
    if change=='kind':spec['entries']['old']['kind']='primitive'
    if change=='missing':bases['base']['definitions']={}
    if change=='cycle':bases['base']=dict(inherited_meaning_basis='latest')
    with pytest.raises(ValueError):semantic_spellings(spec,'spellings',bridge,bases.__getitem__)


def test_the_actual_seventeen_words_add_no_native_declarations_or_meanings():
    ctx=discourse_context();prior=reference_context()
    assert ctx.document==prior.document
    assert ctx.declarations==prior.declarations
    assert ctx.document['statements']==[]
    spec=json.loads((ROOT/DISCOURSE_SPELLINGS).read_text(encoding='utf-8'))
    assert len(spec['entries'])==17
    assert sum(r['kind']=='definition' for r in spec['entries'].values())==7
    for old in spec['entries']:
        token=inputs()['bridge']['mapping'][old]
        assert ctx.words[token]==prior.words[token]
        assert len(ctx.parts[token])<len(prior.parts[token])
    for parts,token in prior.full_spellings.items():
        assert ctx.spellings[parts]==token
