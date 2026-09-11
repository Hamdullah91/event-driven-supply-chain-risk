# SEC Relation Annotation Guide

This guide defines the gold-standard annotation process for evaluating the SEC relation extractor.

## Unit of annotation

Each JSONL row contains one real sentence sampled from the 27 production SEC filings.

Set:

- `annotation_status` to `REVIEWED` after adjudication.
- `gold_relations` to a JSON list. Use an empty list when the sentence contains no supported graph relation.

Do not label a relation unless the sentence itself supports it.

## Allowed relationships

- `DEPENDS_ON`
- `SUPPLIES`
- `PRODUCES`
- `USES`
- `OPERATES`
- `OWNS`

## Allowed endpoint types

- `Company`
- `Facility`
- `Product`
- `Material`
- `Technology`
- `Location`

## Canonical relation format

```json
{
  "subject": "AMD",
  "subject_type": "Company",
  "relationship": "DEPENDS_ON",
  "object": "TSMC",
  "object_type": "Company"
}
```

## Rules

1. Resolve `we`, `our`, `the company`, and equivalent filing references to the filing company.
2. Preserve direction. Example: `NVIDIA is supplied by TSMC` is `TSMC SUPPLIES NVIDIA`.
3. A sourcing/reliance statement on another company is `DEPENDS_ON`.
4. A company manufacturing a concrete product is `PRODUCES`.
5. Do not create relations from generic nouns such as `that`, `both`, `range`, `period`, `sale`, or `portfolio`.
6. Do not create Company-to-same-Company self-relations.
7. Business units known to belong to a parent company should use the configured organizational rollup.
8. Legally separate verified counterparties remain separate organizations.
9. If an organization is plausible but not verified, do not force a canonical Company identity; treat it as a review candidate outside the production graph.
10. If the sentence is hypothetical or risk-oriented, label a relation only when it still states a concrete dependency/production fact rather than a merely possible future event.

## Negative example

A sentence that merely says supply-chain disruption could occur, without naming a concrete dependency or production relation, receives:

```json
"gold_relations": []
```

## Evaluation target

The generated sample contains 250 sentences using a fixed random seed so results are reproducible. Report exact resolved-relation Precision, Recall, F1, and exact-sentence accuracy.

The historical graph baseline (`12/27` companies with SEC edges and `35` unique relationships) is retained only as coverage context. It is not a sentence-level gold-standard metric and must not be compared numerically to Precision/Recall/F1 as if they were the same measure.
