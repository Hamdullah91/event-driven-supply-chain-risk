# Event Classification Labeling Guide

## 1. SUPPLY_DISRUPTION

Use when the primary event causes shortage, delay, reduced availability,
transport disruption, sourcing failure, or inability to obtain required
materials/components.

Examples:
- Semiconductor shortages delay vehicle production.
- Lithium deliveries to battery manufacturers are delayed.
- Port congestion prevents components from reaching manufacturers.

Do not use when the primary event is the shutdown of a specific physical
facility. Use FACILITY_OUTAGE instead.


## 2. REGULATION_CHANGE

Use when a government or regulatory authority introduces or changes
regulations, compliance requirements, safety rules, environmental rules,
or industry standards.

Examples:
- New battery recycling regulations are introduced.
- Semiconductor manufacturers face new chemical handling requirements.
- Aerospace suppliers must comply with stricter safety standards.


## 3. FACILITY_OUTAGE

Use when a factory, plant, fab, mine, warehouse, or other physical facility
stops or significantly reduces operations.

Typical causes:
- Fire
- Flood
- Earthquake
- Explosion
- Power failure
- Equipment failure

Examples:
- A fire shuts down a semiconductor fabrication plant.
- Flooding suspends production at a battery factory.


## 4. TECHNOLOGY_EMBARGO

Use when access to specific technology, advanced equipment, technical
capabilities, intellectual property, or advanced technological products
is prohibited or restricted.

Examples:
- Advanced lithography equipment exports are banned.
- Companies are prohibited from supplying advanced AI chips.
- Semiconductor fabrication technology is placed under export controls.


## 5. TRADE_POLICY_CHANGE

Use when tariffs, sanctions, import/export rules, customs policies,
licensing requirements, or other cross-border trade policies change.

Examples:
- A new tariff is imposed on imported EV batteries.
- New sanctions target industrial suppliers.
- New export licensing requirements are introduced.

Do not use QUOTA_CHANGE when the event is primarily a policy/rule change
without a specific quantitative limit.


## 6. QUOTA_CHANGE

Use when a specific quantitative limit on production, exports, imports,
or allocation is introduced, increased, or decreased.

Examples:
- The annual rare-earth export quota is reduced.
- Lithium export quotas are increased.
- Cobalt production is limited to a specified amount.


# Ambiguous Event Rule

Assign the label representing the PRIMARY event described by the text.

Examples:

"China reduces graphite exports to 70,000 tonnes."
→ QUOTA_CHANGE

"China introduces a licensing requirement for graphite exports."
→ TRADE_POLICY_CHANGE

"The export of advanced semiconductor manufacturing technology is banned."
→ TECHNOLOGY_EMBARGO

"A fire shuts down a supplier's factory."
→ FACILITY_OUTAGE

"The shutdown causes customers to experience component shortages."
→ SUPPLY_DISRUPTION