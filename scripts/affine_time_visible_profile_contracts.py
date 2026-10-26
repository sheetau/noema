"""Preserved coefficient alternatives and brevity contracts."""
SOURCE_RELATIONS={'zet': 'unexcludedcoefficientalternative', 'zex': 'assumedforbrevity'}
CONTRACTS={'unexcludedcoefficientalternative': {'parameters': ['individual', 'situation', 'situation'],
                                      'result': 'truth',
                                      'arguments': ['agent', 'stage', 'alternative'],
                                      'meaning_ja': '主体がその段階で排除していない係数関数の候補状況。候補の選び方を明示する関係。'},
 'assumedforbrevity': {'parameters': ['individual', 'individual', 'individual', 'situation'],
                       'result': 'truth',
                       'arguments': ['node', 'author', 'scope', 'context'],
                       'meaning_ja': '著者がその仮定を記述の簡潔さのために採ると位置付ける。仮定の必然性や結論の証明ではない。'}}
