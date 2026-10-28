"""General closing-item locations and named-presentation records."""
CONTRACTS={}
SOURCE_RELATIONS={}
MATH_ALIASES={}
EXTRA={'closingreference': {'parameters': ['situation', 'number'],
                      'result': 'individual',
                      'arguments': ['context', 'closing_item'],
                      'meaning_ja': '同じ対象文章の提示文脈における、本文後の独立した後付項目を印刷順に1から数えた位置への参照。署名や日付などの項目を本文段落・前付・著者注と区別する。項目の内容・著者性・記載の真理を位置から導かない。'},
 'closingpresentationrecord': {'parameters': ['situation', 'number'],
                               'result': {'kind': 'function',
                                          'parameters': [{'kind': 'function',
                                                          'parameters': ['individual',
                                                                         'individual',
                                                                         'individual',
                                                                         'individual'],
                                                          'result': 'individual'}],
                                          'result': 'individual'},
                               'arguments': ['context', 'closing_item'],
                               'meaning_ja': '同じ提示文脈の指定した後付項目に結び付けて照合する名称使用・名称個体・対象個体・文書個体を、この順に保持する参照の組。どの選択関数にも同じ4値を同順で渡す。前付の名称表示とは位置区分を分け、名称使用の成立、名称の適用、著者役割や自筆性を参照値から導かない。'}}
