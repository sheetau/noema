"""General closed energy accounting and a rational reference contract."""
CONTRACTS={'closedenergyexchange': {'parameters': [],
                          'result': {'kind': 'function',
                                     'parameters': ['individual',
                                                    'individual',
                                                    'individual',
                                                    'individual',
                                                    'individual',
                                                    'individual',
                                                    'individual',
                                                    'situation'],
                                     'result': 'truth'},
                          'arguments': [],
                          'meaning_ja': '同じ過程・粒子・場・系・両端・単位・文脈で、記述した取り出し・運動エネルギー変化・放射以外の移転や内部変化がない設定。'}}
SOURCE_RELATIONS={'zrgclosed':'closedenergyexchange'}
MATH_ALIASES={}
EXTRA={'describedrationalreference': {'parameters': ['individual',
                                               'individual',
                                               {'kind': 'description',
                                                'result': {'kind': 'function',
                                                           'parameters': ['number', 'situation'],
                                                           'result': 'truth'}},
                                               'situation'],
                                'result': 'number',
                                'arguments': ['document', 'node', 'role_description', 'context'],
                                'meaning_ja': '同じ文書・箇所・提示文脈で、閉じた役割関係の記述に結び付けて照合する有理数候補への参照。役割は本文で定義する。参照の取得から役割の成立、候補の存在の証明や唯一性を導かず、引用した役割を実行しない。未知の参照を拒否し、候補値や正値性を補わない。'}}
