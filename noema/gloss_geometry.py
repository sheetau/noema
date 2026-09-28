"""Unfitted geometry diagnostics for a fixed candidate bank, not probabilities."""
import torch

from .semantics import require

METHODS = ('dot', 'cosine', 'projected_cosine', 'centered_dot')


def _validate(query, bank):
    require(isinstance(query, torch.Tensor) and isinstance(bank, torch.Tensor), 'Expected tensors')
    require(query.ndim == bank.ndim == 2 and query.shape[1] == bank.shape[1]
            and min(*query.shape, *bank.shape) > 0, 'Invalid geometry shapes')
    require(query.is_floating_point() and bank.dtype == query.dtype and bank.device == query.device,
            'Geometry dtype or device mismatch')
    require(bool(torch.isfinite(query).all()) and bool(torch.isfinite(bank).all()), 'Non-finite geometry input')


def _unit(value):
    norm = value.norm(dim=-1, keepdim=True)
    require(bool(torch.isfinite(norm).all()) and bool((norm > 0).all()), 'Zero or overflowing vector norm')
    return value / norm


def remove_direction(value, direction):
    residual = value - (value @ direction)[:, None] * direction
    # Cancellation near the input scale must not turn rounding noise into a direction.
    require(bool((residual.norm(dim=-1) > 32 * torch.finfo(value.dtype).eps * value.norm(dim=-1)).all()),
            'Degenerate projected vector')
    return residual


def geometry_scores(query, bank):
    _validate(query, bank)
    q_unit, g_unit = _unit(query), _unit(bank)
    mean = bank.mean(0, keepdim=True)
    direction = _unit(mean)[0]
    projected_q = _unit(remove_direction(query, direction))
    projected_g = _unit(remove_direction(bank, direction))
    matrices = {'dot': query @ bank.T, 'cosine': q_unit @ g_unit.T,
                'projected_cosine': projected_q @ projected_g.T,
                'centered_dot': query @ (bank - mean).T}
    require(all(bool(torch.isfinite(v).all()) for v in matrices.values()), 'Non-finite geometry score')
    return matrices


def geometry_summary(query, bank):
    _validate(query, bank)
    q_unit, g_unit = _unit(query), _unit(bank)
    direction = _unit(bank.mean(0, keepdim=True))[0]

    def stats(values):
        require(values.numel() > 0, 'Empty geometry statistic')
        return {'count': values.numel(), 'min': values.min().item(),
                'mean': values.mean().item(), 'max': values.max().item()}

    pair_cos = g_unit @ g_unit.T
    pairs = torch.triu_indices(len(bank), len(bank), offset=1, device=bank.device)
    require(len(bank) >= 2, 'At least two definitions required for pair statistics')
    return {'query_norm': stats(query.norm(dim=-1)), 'definition_norm': stats(bank.norm(dim=-1)),
            'query_common_energy_fraction': stats((q_unit @ direction).square()),
            'definition_common_energy_fraction': stats((g_unit @ direction).square()),
            'definition_pair_cosine': stats(pair_cos[pairs[0], pairs[1]])}
