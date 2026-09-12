# Risk Propagation Engine

## Distance-decay convention

The engine uses the path-level formula:

`R(P) = R0 * product(w_i) * lambda ** (h - 1)`

where:

- `R0` is the event-derived initial risk.
- `w_i` is the dependency weight of each supply relationship on the path.
- `h` is the downstream company hop distance, limited to 1..3.
- `lambda` is the configurable distance-decay factor in `(0, 1]`.

The exponent is `h - 1`, not `h`, because hop 1 is the first directly exposed downstream company and receives no additional distance penalty. With the provisional baseline `lambda = 0.70`:

- hop 1: `1.00`
- hop 2: `0.70`
- hop 3: `0.49`

Relationship dependency strength and graph distance are deliberately separate. A strong relationship can preserve more risk along a path, while distance always attenuates indirect exposure.

## Calibration policy

`lambda = 0.70` is a provisional calibration baseline, not a learned or historically proven parameter. Day 42 sensitivity analysis evaluates candidate values `0.50, 0.60, 0.70, 0.75, 0.80, 0.90`. Day 44 scenario evaluation should determine whether the baseline should be revised using plausible downstream rankings and, where labels are available, ranking metrics such as Precision@K, Recall@K, or NDCG@K.

## Missing dependency weights

The graph repository currently falls back to `1.0` when `dependency_weight` is absent and records `weight_source = "default"`. This preserves Days 39-41 behavior and keeps the assumption auditable. It must not be interpreted as an empirically validated maximum dependency. A later calibration step should compare alternative missing-weight policies before final evaluation.

## Separation of responsibilities

Day 42 computes risk for an individual path. Multi-path and multi-event aggregation are intentionally deferred to Day 43 so path attenuation and cumulative exposure can be tested independently.
