"""Text location of frontmatter items, distinct from their content or referents."""
CONTRACTS={}
SOURCE_RELATIONS={}
MATH_ALIASES={}
EXTRA={'frontmatterreference': {'parameters': ['situation', 'number'],
                          'result': 'individual',
                          'arguments': ['context', 'frontmatter_item'],
                          'meaning_ja': '指定した前付提示文脈で、前付項目の出現順を1から数えて指定した談話箇所を指す。表題・著者表示などを本文段落や本文見出しの番号へ混ぜない。同じ文脈の同じ位置は同じ箇所を指し、異なる位置は異なる項目の出現である。項目の主題、名称の対象、著者役割、表示内容の真理はこの位置参照から導かない。'}}
