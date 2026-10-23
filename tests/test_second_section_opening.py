from scripts import check_second_section_opening as c

def test_topics():assert c.topic_checks()
def test_premises():assert c.premise_checks()
def test_introduction():assert c.introduction_checks()
def test_presentation():assert c.presentation_checks()
def test_structure():assert c.structure_checks()
