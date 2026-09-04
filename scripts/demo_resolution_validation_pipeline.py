from src.nlp.entity_resolution.integration import (
    resolve_extracted_companies,
)
from src.nlp.validation.resolution_integration import (
    ResolvedRelationshipInput,
    validate_resolved_relationships,
)


resolved = resolve_extracted_companies(
    [
        "NVIDIA",
        "TSMC",
    ]
)

relationships: list[ResolvedRelationshipInput] = []

for company in resolved:
    if company.canonical_name == "NVIDIA Corporation":
        relationships.append(
            ResolvedRelationshipInput(
                subject=company,
                relationship="USES",
                object_name="Silicon",
                object_type="Material",
            )
        )

        relationships.append(
            ResolvedRelationshipInput(
                subject=company,
                relationship="LOCATED_IN",
                object_name="California",
                object_type="Location",
            )
        )

    elif (
        company.canonical_name
        == "Taiwan Semiconductor Manufacturing Company"
    ):
        relationships.append(
            ResolvedRelationshipInput(
                subject=company,
                relationship="SUPPLIES",
                object_name="NVIDIA Corporation",
                object_type="Company",
            )
        )


result = validate_resolved_relationships(relationships)

print("VALID")
print("-----")

for relationship in result.valid:
    print(
        relationship.subject,
        f"-[{relationship.relationship}]->",
        relationship.object,
    )

print()

print("REJECTED")
print("--------")

for rejected in result.rejected:
    candidate = rejected.candidate

    print(
        candidate.subject,
        f"-[{candidate.relationship}]->",
        candidate.object,
    )

    print("Reason:", rejected.reason)