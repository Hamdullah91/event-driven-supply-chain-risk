# DistilBERT Event Dataset Strategy

## Target

Build a balanced six-class supply-chain event classification dataset.

Target size:

- Initial pilot: 120 examples
- Intermediate: ~600 examples
- Target: ~1,200 examples
- Approximately 200 examples per class

The final size may change based on validation performance and data quality.

---

## Event Classes

1. SUPPLY_DISRUPTION
2. REGULATION_CHANGE
3. FACILITY_OUTAGE
4. TECHNOLOGY_EMBARGO
5. TRADE_POLICY_CHANGE
6. QUOTA_CHANGE

The canonical label-to-ID mapping is stored in:

data/event_classifier/label_map.json

---

## Data Sources

The dataset will contain three kinds of examples.

### 1. Real News Examples

Real supply-chain event text collected from legitimate news sources.

Store provenance where available:

- source
- source_url
- publication date

Real examples provide realistic journalistic language.

### 2. Synthetic Examples

Manually or AI-generated examples used to improve class balance and linguistic diversity.

Synthetic examples must be human-reviewed before inclusion.

Store:

source = "synthetic"

Synthetic data must not simply repeat obvious label keywords.

### 3. Hard / Ambiguous Examples

Examples deliberately designed to distinguish similar classes.

Important boundaries include:

- FACILITY_OUTAGE vs SUPPLY_DISRUPTION
- TRADE_POLICY_CHANGE vs TECHNOLOGY_EMBARGO
- TRADE_POLICY_CHANGE vs QUOTA_CHANGE
- REGULATION_CHANGE vs TRADE_POLICY_CHANGE

These examples should avoid obvious label-specific vocabulary where possible.

---

## Quality Requirements

### Class Balance

Classes should remain approximately balanced.

Avoid situations such as:

SUPPLY_DISRUPTION = 500
QUOTA_CHANGE = 50

### Linguistic Diversity

Examples should vary in:

- sentence structure
- vocabulary
- company/entity names
- geographic locations
- event causes
- industries
- article style

### Industry Coverage

Examples should represent:

- Semiconductors
- EV batteries
- Aerospace & electronics

### Keyword Leakage

Do not allow the classifier to depend entirely on words such as:

quota
tariff
regulation
embargo
shortage
outage

Some examples should naturally contain these terms, while others should
express the same event without them.

### Duplicate Prevention

Exact duplicate text is prohibited.

Highly similar paraphrases should also be minimized.

---

## Provenance

Each record should contain at minimum:

- id
- text
- label
- source

Where applicable:

- source_url
- published_at

Example:

{
  "id": "evt_000121",
  "text": "...",
  "label": "FACILITY_OUTAGE",
  "source": "synthetic"
}

---

## Dataset Construction Process

Collect / generate candidate
        ↓
Assign event label
        ↓
Apply LABELING_GUIDE.md
        ↓
Human review
        ↓
Add provenance
        ↓
Validate dataset
        ↓
Run quality audit
        ↓
Accept into raw dataset

---

## Important Rule

Dataset size must never be increased at the expense of label quality.

A smaller, diverse, consistently labeled dataset is preferable to a large
dataset containing repetitive or contradictory examples.