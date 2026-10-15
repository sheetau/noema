from copy import deepcopy
from itertools import product
import json
from pathlib import Path

import pytest

from noema.closed_document import prune_document, certificate, verify_certificate, main
from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from noema.script import transcribe
from noema.semantics import SemanticError
from scripts.compose_manuscript_pruning import ROOT, SOURCES, MANIFEST, REVIEW, PREVIOUS_REVIEW, build


def values(doc, primitives):
    return [r['value'] for r in evaluate_document(doc, individuals=('person',), situations=('now',),
        primitives={d['name']: primitives[d['name']] for d in doc['declarations'] if d['kind']=='primitive'})]


def sample():
    return parse('p:r aa[] c.r ab[] c.r unused[] c.d first[] c[k aa[]].d second[] c[k aa[]].'
        'd template[] i b[h[c] c][r b[i[x c][w[v x][s[r[k first[]]]]]]].'
        'd made[] i b[c][o a[k template[]][r[k ab[]]]].'
        'q[s[k made[]]].q[u[e[r[p first]][r[p second]]]].q[s[k made[]]].')


@pytest.mark.parametrize('edition',list('hijklmnop'))
def test_edition_is_preserved_without_implicit_promotion(edition):
    doc=parse(edition+':r aa[] c.r unused[] c.q[k aa[]].')
    result=prune_document(doc)
    assert result.document['schema_version']==doc['schema_version']
    assert result.document['lexicon_version']==doc['lexicon_version']
    assert parse(format_graph(result.document,'compact'))==result.document
    assert result.removed_symbols==['unused']


@pytest.mark.parametrize('a,b', list(product((False, True), repeat=2)))
def test_constructed_quotes_keep_results_and_distinct_definition_identity(a,b):
    doc=sample();before=deepcopy(doc);result=prune_document(doc)
    model={'aa':lambda:a,'ab':lambda:b,'unused':lambda:False}
    assert values(doc,model)==values(result.document,model)==[a and b,True,a and b]
    assert doc==before and result.document['statements']==doc['statements']
    assert result.removed_symbols==['unused']
    assert {'first','second','template','made'} <= set(result.retained_symbols)
    assert prune_document(result.document).document==result.document


def test_nested_quotes_lifting_folds_and_assumption_scopes_are_dependencies():
    doc=parse('p:r aa[] c.r unused[] c.d seq[] j[c][l[c][k aa[]]].'
        'd folded[] c[q[k seq[]][k aa[]][i[state c item c][x[v state][v item]]]].'
        'd lifted[] i[i[h[] c]][o r[r[p folded]]].'
        'a[k aa[]][q[e[k lifted[]][r[r[p folded]]]].q[k folded[]].].')
    result=prune_document(doc)
    assert result.retained_symbols==['aa','seq','folded','lifted']
    assert result.document['statements']==doc['statements']
    for notation in ('full','compact'):
        text=format_graph(result.document,notation)
        assert parse(text)==parse(transcribe(text,alphabet='v2'))==result.document


def test_quoted_inputs_are_retained_without_evaluation():
    doc=parse('p:r aa[] c.r unused[] c.d copied[] c[k aa[]].'
        'q[e[r c[r b[r[p copied]]]][r c[r b[r[p copied]]]]].')
    def forbidden():raise AssertionError('Quoted content was executed')
    result=prune_document(doc)
    assert result.retained_symbols==['aa','copied']
    assert values(result.document,{'aa':forbidden})==[True]


def test_extra_library_roots_do_not_confuse_variables_with_declarations():
    doc=parse('p:r aa[] c.r ab[] c.d ac[ab c] c[v ab].q[k aa[]].')
    result=prune_document(doc,roots=['ac','ac'])
    assert result.roots==['ac'] and result.retained_symbols==['aa','ac']
    library=parse('p:r aa[] c.d ab[] c[k aa[]].')
    assert prune_document(library,roots=['ab']).retained_symbols==['aa','ab']
    with pytest.raises(SemanticError,match='Empty document'):prune_document(library)


@pytest.mark.parametrize('roots', ('aa',['missing'],[True]))
def test_invalid_roots_are_rejected(roots):
    with pytest.raises(SemanticError):prune_document(sample(),roots=roots)


def test_invalid_unused_declaration_is_not_hidden_by_pruning():
    doc=parse('p:r aa[] c.d unused[] c[k aa[]].q[k aa[]].')
    doc['declarations'][1]['body']['symbol']='missing'
    with pytest.raises(SemanticError):prune_document(doc)


@pytest.mark.parametrize('tamper', ('statement','name','rank','record','completion'))
def test_certificate_rejects_lost_meaning_and_forged_claims(tamper):
    doc=sample();result=prune_document(doc);record=certificate(doc,result);out=deepcopy(result.document)
    assert verify_certificate(doc,out,record)==result
    if tamper=='statement':out['statements'].pop()
    elif tamper=='name':out['declarations'][2]['name']='changed'
    elif tamper=='rank':out['declarations'][-1]['result']['rank']=0
    elif tamper=='record':record['statement_ast_sha256'].pop()
    else:record['semantic_completion']=True
    with pytest.raises(SemanticError):verify_certificate(doc,out,record)


def test_cli_keeps_all_statements_and_preserves_existing_files(tmp_path):
    source=tmp_path/'source.noema';output=tmp_path/'output.noema';manifest=tmp_path/'manifest.json'
    source.write_text(format_graph(sample(),'compact'),encoding='utf-8')
    main(['-i',str(source),'-o',str(output),'--manifest',str(manifest)])
    record=json.loads(manifest.read_text(encoding='utf-8'))
    verify_certificate(sample(),parse(output.read_text(encoding='utf-8')),record['certificate'])
    before=output.read_bytes()
    with pytest.raises(SystemExit):main(['-i',str(source),'-o',str(output)])
    assert output.read_bytes()==before
    fresh=tmp_path/'fresh.noema'
    with pytest.raises(SystemExit):main(['-i',str(source),'-o',str(fresh),'--manifest',str(manifest)])
    assert not fresh.exists()
    with pytest.raises(SystemExit):main(['-i',str(source),'-o',str(fresh),'--manifest',str(fresh)])
    assert not fresh.exists()


def test_certificate_pins_even_unreachable_source_declarations():
    doc=sample();result=prune_document(doc);record=certificate(doc,result)
    changed=deepcopy(doc);changed['declarations'][2]['name']='otherunused'
    assert prune_document(changed).document==result.document
    with pytest.raises(SemanticError):verify_certificate(changed,result.document,record)


@pytest.mark.parametrize('work', tuple(SOURCES))
def test_current_manuscripts_preserve_every_statement_and_retained_declaration(work):
    source,output=SOURCES[work]
    original=parse((ROOT/source).read_text(encoding='utf-8'))
    actual=parse((ROOT/output).read_text(encoding='utf-8'))
    record=json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))['works'][work]
    verify_certificate(original,actual,record['certificate'])
    assert actual['statements']==original['statements']
    assert len(actual['declarations'])<len(original['declarations'])
    assert record['after_characters']<record['before_characters']
    assert set(record['source_aligned_roots']) <= {d['name'] for d in actual['declarations']}
    assert record['source_aligned_roots']==record['certificate']['roots']


def test_reproducible_artifacts_preserve_all_open_obligations():
    assert all((ROOT/p).read_text(encoding='utf-8')==text for p,text in build().items())
    old=json.loads((ROOT/PREVIOUS_REVIEW).read_text(encoding='utf-8'))
    new=json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))
    for key in ('obligations','templates','semantic_completion','counts_as_translated_coverage','evidence_files'):
        assert old[key]==new[key]
