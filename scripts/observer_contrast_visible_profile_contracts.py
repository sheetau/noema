"""Preserved scoped-claim and explicit-polarity judgment contracts."""
SOURCE_RELATIONS={'uh': 'presentsclaimunderassumption', 'zba': 'judgescontentpolarity'}
CONTRACTS={'presentsclaimunderassumption': {'parameters': ['individual',
                                                 'individual',
                                                 {'kind': 'description', 'result': 'content'},
                                                 'individual',
                                                 'situation'],
                                  'result': 'truth',
                                  'arguments': ['node', 'author', 'content_description', 'scope', 'context'],
                                  'meaning_ja': '著者が指定の文章箇所で内容の記述を、指定した仮定の範囲内の主張として提示する。文書全体の無条件の断言へ昇格させない。'},
 'judgescontentpolarity': {'parameters': ['individual',
                                          {'kind': 'description', 'result': 'content'},
                                          'truth',
                                          'situation'],
                           'result': 'truth',
                           'arguments': ['observer', 'description', 'polarity', 'context'],
                           'meaning_ja': '観測者が指定内容を肯定または否定と判断するという関係。想定された運動文脈で用い、現実の観測の発生や正当な推論をそれだけでは主張しない。'}}
