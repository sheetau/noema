"""Connect written works to actual or intended carrier configurations."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT = 'examples/v016/kant-pastoral-roles.noema'
PARENT_BASIS = 'data/pastoral-roles-basis-v1.json'
FULL = 'examples/v016/kant-book-form.noema'
CORE = 'examples/v016/book-form-core.noema'
LIBRARY = 'examples/v016/intended-carrier-forms.noema'
BASIS = 'data/book-form-basis-v1.json'
ANNOTATIONS = 'data/book-form-identifiers-v1.json'
PRIMITIVES = {
    'hzwv': (['carrier', 'scene'], 'その媒体は、複数の薄い面状の葉を順序のある一つのまとまりとして扱えるように集めた構成を持つ。綴じられた集合も、同じまとまりとして用意された未製本の集合も含む。紙や羊皮紙という材質、印刷技法、文字の有無、内容の真理・長さはこの関係だけから要求しない。一枚だけの面、単なる壁面や、互いに関係のない紙片の集積とは区別する。'),
    'hzww': (['work', 'carrier_form_description', 'scene'], 'その作品の制作・提供上の構想で、記述された構成の媒体にその作品を記録として実現することが予定されている。任意の読者がそうなると望むことや、別作品の制作予定ではない。実際の製作・現在のその形の媒体の存在・将来の成功を含意しない。対象となる構成記述を保持し、異なる構成の予定で置き換えない。'),
}
MEANINGS = {
    'rqxn': '同じ作品の読める記録が同じ媒体に存在し、その媒体が引数として指定した構成条件を現在満たす。作品・記録・媒体・状況をrqxkで共有し、別の記録の媒体の形を寄せ集めない。',
    'rqxo': '葉を一つに集めた構成hzwvの媒体で作品を現在参照できるrqxn、またはその同じ構成の記述を対象に作品を実現する制作上の予定hzwwがある。実際と予定のどちらでもよく、両方とも許す。予定から実在や成功は導かない。',
    'rqxp': '一つにまとめた記された作品scであり、外部の媒体に保持され参照できるsdを満たす。旧slの広い条件を保存し、媒体の形はまだ限定しない。',
    'sl': 'rqxpの参照可能な記された作品であり、葉を一つに集めた媒体構成hzwvで実際に参照できるか、その構成での実現が制作上予定されている。書物を利用する例の内容としての読みへ、実際または予定された媒体の形を接続する。製本済み・印刷済み・本人による所有は要求しない。分量や刊行上の独立性の慣習、他の語義の全条件は未確認。',
}


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not (set(PRIMITIVES) | set(MEANINGS) - {'sl'}) & set(old.entries)
    at = next(i for i, d in enumerate(doc['declarations']) if d['name'] == 'sl')
    prefix = deepcopy(doc); prefix.update(declarations=doc['declarations'][:at], statements=[])
    raw = deepcopy(old.entries['sl']['declaration']); raw['name'] = 'rqxp'; prefix['declarations'].append(raw)
    fields = 'work a form h[a d] c scene d records h[a a d] c carries h[a a d] c readable h[a d] c'
    text = 'r hzwv[a d] c.r hzww[a i[h[a d] c] d] c.'
    text += 'd rqxn[' + fields + '''] c[
 g carrier a[w[k rqxk[v work v carrier v scene v records v carries v readable]][c[v form][v carrier v scene]]]
].'''
    text += '''d rqxo[work a scene d] c[
 x[k rqxn[v work p hzwv v scene p hzwr p hzws p hzwt]][k hzww[v work r[p hzwv] v scene]]
].
d sl[work a scene d] c[w[k rqxp[v work v scene]][k rqxo[v work v scene]]].'''
    parsed = parse(format_graph(prefix, 'compact') + text)
    doc['declarations'] = parsed['declarations'] + doc['declarations'][at + 1:]
    doc = parse(format_graph(doc, 'compact'))
    basis = dict(status='actual_or_intended_carrier_form', document=FULL, revises_document=PARENT,
        revises_meaning_basis=PARENT_BASIS, primitives={}, definitions={}, predecessor_source_sha256=old.source_sha256,
        limitations=['歴史辞典が区別する媒体・内容・将来その形にする原稿を、この箇所の内容としての読みへ接続する。唯一の読解や書物全語義の定義とはしない。',
            '語義の分量と刊行上の独立性は未確認。原文へ固定ページ数、現代の媒体規格、製本済み条件を追加しない。',
            '予定された形だけでは実在を要求しないが、本文slでは旧来の現在参照可能な作品rqxpも必要。まだ何も記されていない構想だけは利用例にしない。',
            '葉・配置・制作予定の基礎意味規約は残る。第二段落全体と二作品全文の意味確認は未完。'],
        unresolved=[dict(basis=r['basis'], historical_caveats=r['caveats']) for r in old.lineage])
    for d in doc['declarations']:
        n = d['name']
        if d['kind'] == 'primitive':
            labels, meaning = PRIMITIVES[n] if n in PRIMITIVES else (old.entries[n]['arguments'], old.entries[n]['meaning_ja'])
            basis['primitives'][n] = dict(parameters=d['parameters'], result=d['result'], arguments=labels, meaning_ja=meaning)
        else:
            basis['definitions'][n] = MEANINGS[n] if n in MEANINGS else old.entries[n]['meaning_ja']
    core = deepcopy(doc); core['statements'] = [doc['statements'][4]]
    core['declarations'] = closure(doc, _references(core['statements']))
    lib = deepcopy(doc); lib.update(declarations=closure(doc, ['rqxn']), statements=[])
    body = format_graph(doc, 'compact') + '\n'
    ann = json.loads((ROOT / 'data/pastoral-roles-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', LIBRARY: format_graph(lib, 'compact') + '\n',
        BASIS: enc(basis), ANNOTATIONS: enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for p, s in build().items():
        write_exact(ROOT / p, s)
    print('Actual and intended carrier forms composed', flush=True)


if __name__ == '__main__':
    main()
