"""Connect an institutional appointment to the same role and community duty."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT = 'examples/v016/kant-service-roles.noema'
PARENT_BASIS = 'data/service-roles-basis-v1.json'
FULL = 'examples/v016/kant-appointed-roles.noema'
CORE = 'examples/v016/appointed-roles-core.noema'
LIBRARY = 'examples/v016/appointed-responsibilities.noema'
BASIS = 'data/appointed-roles-basis-v1.json'
ANNOTATIONS = 'data/appointed-roles-identifiers-v1.json'
PRIMITIVES = {
    'hzxf': (['person', 'role', 'community', 'scene'], 'この共同体の制度・慣行に従い、この人が同じ役割に任じられ、その任用がこの状況でも有効である。自己申告や単なる活動実績とは分ける。制度の正当性、本人の能力、現在の活動、特定の任命儀礼は要求しない。共同体・任用された役割・時点を明示する。'),
    'hzxg': (['role', 'provider_community_activity_description', 'community', 'scene'], 'この共同体では、この役割に、記述された活動を担う公的な責務が制度上委ねられている。活動の第一引数は役割の担い手、第二引数は同じ共同体である。援助可能な技能、私的な好み、臨時の自主活動とは分ける。現に活動することや成功、個別の権限の全内容は含めない。'),
    'hzxh': (['act', 'community', 'scene'], 'この行為の構成内容は、同じ宗教共同体の公の宗教的奉仕・礼拝であり、共同体の精神的な安寧のための宗教上の教えや実践を担うものである。個人の私的な信仰・一般的な助言・宗教施設の非宗教的な維持作業だけとは区別する。公的とは共同体に関わる位置付けであり、国家の承認や全員の立入自由を要求しない。行為の生起、参加者、教義の真実性、成功は別条件である。歴史資料の広いöffentlicher Gottesdienstの読みを指定する領域上の基本関係で、宗教行為一般の全分解は主張しない。'),
}
MEANINGS = {
    'rqxx': '同じ担い手・役割・共同体・状況について、役割の保持、受け手の活動への援助機能と主要性、制度上の任用、共同体への活動を担う公的責務を結ぶ。任用だけの別役割や別共同体の責務を混ぜない。活動記述は引用し、その実行は要求しない。',
    'rqxy': '旧spの、宗教上の継続的な援助と、その援助を主要な務めとする役割の保持を保存する。制度上の任用と公的な宗教上の責務はまだ要求しない。',
    'hzxi': '指定された人が同じ共同体の公の宗教的奉仕・礼拝の行為に参加し、その行為が同じ状況で生起する内容。生起dg、参加df、宗教的な行為内容hzxhを同じ行為に結ぶ。役割の責務としてこの内容を引用しても、その時点の実際の遂行を断言しない。',
    'sp': 'rqxmの継続的な宗教上の援助者であり、同じ役割でsoへの援助を主要な務めとし、その役割に同じ共同体から任じられ、共同体の公の宗教的奉仕hzxiを担う責務を持つ。Geistlicherの広い歴史的用法をSeelsorgerへ接続する読み。自称の助言者だけでは足りず、任用された者の現在の活動・能力・信仰・成功は別である。秘跡を扱う資格や特定教派の叙任儀礼を一律に追加しない。',
}


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not (set(PRIMITIVES) | {'rqxx', 'rqxy', 'hzxi'}) & set(old.entries)
    moved = [deepcopy(old.entries[n]['declaration']) for n in ('df', 'dg')]
    doc['declarations'] = [d for d in doc['declarations'] if d['name'] not in ('df', 'dg')]
    at = next(i for i, d in enumerate(doc['declarations']) if d['name'] == 'sp')
    prefix = deepcopy(doc); prefix.update(declarations=doc['declarations'][:at] + moved, statements=[])
    saved = deepcopy(old.entries['sp']['declaration']); saved['name'] = 'rqxy'; prefix['declarations'].append(saved)
    text = '''r hzxf[a a a d] c.r hzxg[a i[h[a a] e] a d] c.r hzxh[a a d] c.
d rqxx[person a task i[h[a] e] service i[h[a a] e] scene d holds h[a a d] c assists h[a i[h[a] e] d] c principal h[a i[h[a] e] d] c appointed h[a a a d] c responsible h[a i[h[a a] e] a d] c] c[
 g role a[g community a[w[c[v holds][v person v role v scene]][w[c[v assists][v role v task v scene]][w[c[v principal][v role v task v scene]][w[c[v appointed][v person v role v community v scene]][c[v responsible][v role v service v community v scene]]]]]]]
].
d hzxi[person a community a] e[b scene[g act a[w[k dg[v act v scene]][w[k df[v person v act v scene]][k hzxh[v act v community v scene]]]]]].
d sp[person a scene d] c[w[k rqxm[v person v scene]][k rqxx[v person r[p so] r[p hzxi] v scene p hzwn p hzwo p hzwu p hzxf p hzxg]]].'''
    parsed = parse(format_graph(prefix, 'compact') + text)
    doc['declarations'] = parsed['declarations'] + doc['declarations'][at + 1:]
    doc = parse(format_graph(doc, 'compact'))
    basis = dict(status='institutional_appointment_and_community_responsibility_connected', document=FULL,
        revises_document=PARENT, revises_meaning_basis=PARENT_BASIS, primitives={}, definitions={},
        predecessor_source_sha256=old.source_sha256,
        limitations=['公的な宗教上の責務を担う者という広い歴史的用法を選ぶ。全教派・時代の職制の共通分類は主張しない。',
            '任用・責務の基本関係は制度上の事実を入力として解釈する。自動的な自然言語の分類器ではない。',
            '公の宗教的奉仕の内容hzxhは明示した領域上の基本関係であり、儀礼・教義の全分解は未実装。',
            '条件文全体・第二段落・二作品全文の意味確認は未完。'],
        unresolved=[dict(basis=r['basis'], historical_caveats=r['caveats']) for r in old.lineage])
    for d in doc['declarations']:
        n = d['name']
        if d['kind'] == 'primitive':
            labels, meaning = PRIMITIVES[n] if n in PRIMITIVES else (old.entries[n]['arguments'], old.entries[n]['meaning_ja'])
            basis['primitives'][n] = dict(parameters=d['parameters'], result=d['result'], arguments=labels, meaning_ja=meaning)
        else:
            basis['definitions'][n] = MEANINGS[n] if n in MEANINGS else old.entries[n]['meaning_ja']
    core = deepcopy(doc); core['statements'] = [doc['statements'][i] for i in (4, 42)]
    core['declarations'] = closure(doc, _references(core['statements']))
    lib = deepcopy(doc); lib.update(declarations=closure(doc, ['rqxx']), statements=[])
    body = format_graph(doc, 'compact') + '\n'
    ann = json.loads((ROOT / 'data/service-roles-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', LIBRARY: format_graph(lib, 'compact') + '\n',
        BASIS: enc(basis), ANNOTATIONS: enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for p, s in build().items():
        write_exact(ROOT / p, s)
    print('Appointed responsibilities composed', flush=True)


if __name__ == '__main__':
    main()
