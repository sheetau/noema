from scripts.check_kant_junction_bounds import build_report


def test_actual_bodies_have_identical_svg_and_recovered_native_syntax():
    report=build_report()
    assert [r['statement'] for r in report['cases']]==[5,9]
    for row in report['cases']:
        old,new=row['old'],row['new']
        assert old['svg_sha256']==new['svg_sha256']
        assert old['syntax_sha256']==new['syntax_sha256']
        assert old['exact_svg'] and new['exact_svg'] and old['exact_native'] and new['exact_native']
        assert old['branch_limits']==new['branch_limits']
        assert old['unbranched_paths']==new['unbranched_paths']
    assert report['bounded_profile']['complete_body'] is False
