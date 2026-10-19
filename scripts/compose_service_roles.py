"""Bind provided activities to their provider, recipient, role and skills."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT = 'examples/v016/kant-clinical-roles.noema'
PARENT_BASIS = 'data/clinical-roles-basis-v1.json'
FULL = 'examples/v016/kant-service-roles.noema'
CORE = 'examples/v016/service-roles-core.noema'
LIBRARY = 'examples/v016/provided-activity-roles.noema'
BASIS = 'data/service-roles-basis-v1.json'
ANNOTATIONS = 'data/service-roles-identifiers-v1.json'
PRIMITIVES = {
    'hzw5': (['act', 'provider', 'recipient', 'topic', 'scene'], 'この行為の構成内容として、実施者が受け手について指定事項に対応する措置を施す。実施者自身の操作に加え、その当事者として他者と措置を遂行する場合を含む。評価・指示を述べただけ、無関係な同席、結果が偶然生じただけとは区別する。行為の生起、実施者の参加、措置の適切さ・成功は別条件である。'),
    'hzxa': (['role', 'provider_recipient_activity_description', 'scene'], 'この実践の役割は、記述された二者間の活動を提供する機能を持つ。記述の第一引数はその役割の担い手である実施者、第二引数は受け手の位置に結ぶ。別人が提供する活動への単なる助言とは区別する。役割の機能であり、現在の実行や成功、担い手の能力の充足は要求しない。'),
    'hzxb': (['role', 'provider_recipient_activity_description', 'scene'], '同じ実践の役割で、第一引数を担い手・第二引数を受け手とする指定活動の提供が、主要な務めの一つに位置付けられている。唯一の仕事、時間割合、現に最も多く行ったこととは区別する。機能の存在は別のhzxaで結ぶ。'),
    'hzxd': (['provider', 'provider_recipient_activity_description', 'scene'], 'この人が、記述された二者間の活動の第一引数である実施者として、それを提供するための体系的な学習・経験による専門的知識・技能を備える。第二引数は受け手であり、その人がサービスを受ける技能とは取り違えない。能力の保持と現在の実行・結果の成功・役割の保持・免許は別である。'),
}
MEANINGS = {
    'rqxu': '同じ実施者・受け手・状況について、同じ行為の生起と実施者の参加、同じ事項に対する措置、その事項と受け手の指定関係を結ぶ。別行為の参加や、別人・別事項への措置を合わせない。措置による成功は含意しない。',
    'rqxv': '同じ担い手・役割・状況について、受け手の活動への援助機能と主要性、担い手から受け手へ提供する二者間の活動の機能と主要性、担い手への資格要求を結ぶ。六関係は同じ役割を共有する。記述した活動や資格の内容は実行評価しない。',
    'rqxw': '旧srの、身体の病気・損傷・不調への対応の判断を主要な機能とし、その専門性を求める継続的な役割を保存する。判断に加えて措置の提供を担う条件はまだ含まない。',
    'hzw6': '指定実施者が指定受け手について、身体的な健康shと病気・損傷・不調への対応hzw2に関する同じ事項への措置を施す行為が生起し、その実施者が参加する内容。判断や指示を述べたことだけ、受け手が自分で考えたことだけとは区別する。病気の現存、正しい処置、治癒の成功は含意しない。',
    'hzxe': '本人が、hzw4の臨床上の判断を援助する専門性と、hzw6の措置を実施者として提供する専門性hzxdをともに持つ内容。別人の二つの技能を合算しない。役割の資格記述として引用することと実際の技能を判定することは別である。',
    'sr': '継続的な健康上の援助実践rqxjを担い、同じ社会的役割で、hzw3の判断への援助とhzw6の措置の提供が主要な機能となり、両方の専門性hzxeが資格要件として要求される。医師のこの用例へ判断と実践を接続する読み。担い手の現在の処置・実際の技能・治癒の成功を役割保持から導かず、現代の免許や職種の排他的境界は追加しない。',
}


@lru_cache(None)
def parent():
    return load_catalog(ROOT, PARENT_BASIS)


def build():
    old = parent(); doc = deepcopy(old.document)
    assert not (set(PRIMITIVES) | {'rqxu', 'rqxv', 'rqxw', 'hzw6', 'hzxe'}) & set(old.entries)
    moved = [deepcopy(old.entries[n]['declaration']) for n in ('df', 'dg')]
    doc['declarations'] = [d for d in doc['declarations'] if d['name'] not in ('df', 'dg')]
    at = next(i for i, d in enumerate(doc['declarations']) if d['name'] == 'sr')
    prefix = deepcopy(doc); prefix.update(declarations=doc['declarations'][:at] + moved, statements=[])
    saved = deepcopy(old.entries['sr']['declaration']); saved['name'] = 'rqxw'; prefix['declarations'].append(saved)
    text = '''r hzw5[a a a a d] c.r hzxa[a i[h[a a] e] d] c.r hzxb[a i[h[a a] e] d] c.r hzxd[a i[h[a a] e] d] c.
d rqxu[provider a recipient a scene d occurs h[a d] c participates h[a a d] c acts h[a a a a d] c topic h[a a d] c] c[
 g act a[w[c[v occurs][v act v scene]][w[c[v participates][v provider v act v scene]][g matter a[w[c[v acts][v act v provider v recipient v matter v scene]][c[v topic][v matter v recipient v scene]]]]]]
].
d rqxv[provider a task i[h[a] e] service i[h[a a] e] qualification i[h[a] e] scene d holds h[a a d] c advises h[a i[h[a] e] d] c principal h[a i[h[a] e] d] c provides h[a i[h[a a] e] d] c mainservice h[a i[h[a a] e] d] c requires h[a i[h[a] e] d] c] c[
 g role a[w[c[v holds][v provider v role v scene]][w[c[v advises][v role v task v scene]][w[c[v principal][v role v task v scene]][w[c[v provides][v role v service v scene]][w[c[v mainservice][v role v service v scene]][c[v requires][v role v qualification v scene]]]]]]]
].
d hzw6[provider a recipient a] e[b scene[k rqxu[v provider v recipient v scene p dg p df p hzw5 i[matter a target a situation d][w[k sh[v matter v target v situation]][k hzw2[v matter v target v situation]]]]]].
d hzxe[provider a] e[b scene[w[t[k hzw4[v provider]][v scene]][k hzxd[v provider r[p hzw6] v scene]]]].
d sr[provider a scene d] c[w[k rqxj[v provider v scene]][k rqxv[v provider r[p hzw3] r[p hzw6] r[p hzxe] v scene p hzwn p hzwo p hzwu p hzxa p hzxb p hzwp]]].'''
    parsed = parse(format_graph(prefix, 'compact') + text)
    doc['declarations'] = parsed['declarations'] + doc['declarations'][at + 1:]
    doc = parse(format_graph(doc, 'compact'))
    basis = dict(status='provided_actions_distinguished_from_advice_and_role_holding', document=FULL,
        revises_document=PARENT, revises_meaning_basis=PARENT_BASIS, primitives={}, definitions={},
        predecessor_source_sha256=old.source_sha256,
        limitations=['医師の用例へ判断と措置の提供を結ぶ。役割の機能を述べても、その場で措置や治療が生じたとはしない。',
            '措置の生起と結果の成功は別である。治癒一般の因果機構、全診療形態、全時代・地域の職種境界を完成したとはしない。',
            '以前の文脈読解は固定版への記録として保持する。条件文全体、第二段落、二作品全文の意味確認は未完。'],
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
    lib = deepcopy(doc); lib.update(declarations=closure(doc, ['rqxu', 'rqxv']), statements=[])
    body = format_graph(doc, 'compact') + '\n'
    ann = json.loads((ROOT / 'data/clinical-roles-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL, document_sha256=digest(body.encode('utf-8')))
    enc = lambda x: json.dumps(x, ensure_ascii=False, indent=2) + '\n'
    return {FULL: body, CORE: format_graph(core, 'compact') + '\n', LIBRARY: format_graph(lib, 'compact') + '\n',
        BASIS: enc(basis), ANNOTATIONS: enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for p, s in build().items():
        write_exact(ROOT / p, s)
    print('Provided-activity roles composed', flush=True)


if __name__ == '__main__':
    main()
