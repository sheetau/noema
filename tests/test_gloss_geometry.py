import pytest
import torch

from noema.gloss_geometry import geometry_scores, geometry_summary, remove_direction


def sample():
    return (torch.tensor([[3., 1., 2.], [2., -1., 1.]], dtype=torch.float64),
            torch.tensor([[2., 1., 0.], [2., -1., 1.], [2., 0., -1.]], dtype=torch.float64))


def test_formula_and_centered_dot_preserve_candidate_differences():
    q, g = sample()
    scores = geometry_scores(q, g)
    assert torch.equal(scores['dot'], torch.tensor([[7., 7., 4.], [3., 6., 3.]], dtype=q.dtype))
    assert torch.allclose(scores['centered_dot'], scores['dot'] - (q @ g.mean(0))[:, None])
    assert torch.allclose(scores['cosine'], (q @ g.T) / (q.norm(dim=1)[:, None] * g.norm(dim=1)[None]))
    u = g.mean(0) / g.mean(0).norm()
    qp, gp = remove_direction(q, u), remove_direction(g, u)
    assert torch.allclose(qp @ u, torch.zeros(len(q), dtype=q.dtype))
    assert torch.allclose(scores['projected_cosine'], (qp @ gp.T) / (qp.norm(dim=1)[:, None] * gp.norm(dim=1)[None]))


def test_query_batches_candidate_permutation_and_positive_scale():
    q, g = sample()
    full = geometry_scores(q, g)
    permuted = geometry_scores(q, g[[2, 0, 1]])
    for key in full:
        assert torch.allclose(permuted[key], full[key][:, [2, 0, 1]])
        assert torch.allclose(torch.cat([geometry_scores(row[None], g)[key] for row in q]), full[key])
    scaled = geometry_scores(q * torch.tensor([[2.], [4.]]), g * 7)
    for key in ('cosine', 'projected_cosine'):
        assert torch.allclose(scaled[key], full[key])
    individually_scaled = geometry_scores(q, g * torch.tensor([[2.], [3.], [4.]]))
    assert torch.allclose(individually_scaled['cosine'], full['cosine'])


def test_reject_invalid_or_degenerate_vectors_without_normalizing_noise():
    q, g = sample()
    for bad in (q[:, :2], q.float(), q * float('nan'), q[:0]):
        with pytest.raises(ValueError):
            geometry_scores(bad, g)
    with pytest.raises(ValueError, match='Zero'):
        geometry_scores(q * 0, g)
    with pytest.raises(ValueError, match='Degenerate'):
        geometry_scores(torch.tensor([[1., 0., 0.]], dtype=q.dtype), g)
    with pytest.raises(ValueError, match='Zero'):
        geometry_scores(q, torch.stack([g[0], -g[0]]))


def test_summary_describes_energy_and_all_unique_definition_pairs():
    q, g = sample()
    report = geometry_summary(q, g)
    assert report['definition_pair_cosine']['count'] == 3
    assert report['query_norm']['count'] == 2
    assert report['query_common_energy_fraction']['min'] == pytest.approx(9 / 14)
    assert report['query_common_energy_fraction']['max'] == pytest.approx(4 / 6)
