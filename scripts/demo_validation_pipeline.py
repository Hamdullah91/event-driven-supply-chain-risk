from src.nlp.validation import (
    RelationshipCandidate,
    RelationshipValidationPipeline,
)


candidates = [
    RelationshipCandidate(
        subject="NVIDIA",
        subject_type="Company",
        relationship="uses",
        object="Silicon",
        object_type="Material",
    ),
    RelationshipCandidate(
        subject="TSMC",
        subject_type="Company",
        relationship="SUPPLIES",
        object="NVIDIA",
        object_type="Company",
    ),
    RelationshipCandidate(
        subject="Silicon",
        subject_type="Material",
        relationship="SUPPLIES",
        object="NVIDIA",
        object_type="Company",
    ),
    RelationshipCandidate(
        subject="NVIDIA",
        subject_type="Company",
        relationship="LOCATED_IN",
        object="California",
        object_type="Location",
    ),
]


pipeline = RelationshipValidationPipeline()

result = pipeline.process(candidates)


print("VALID RELATIONSHIPS")
print("-------------------")

for relationship in result.valid:
    print(
        relationship.subject,
        f"-[{relationship.relationship}]->",
        relationship.object,
    )


print()
print("REJECTED RELATIONSHIPS")
print("----------------------")

for rejected in result.rejected:
    candidate = rejected.candidate

    print(
        candidate.subject,
        f"-[{candidate.relationship}]->",
        candidate.object,
    )
    print("Reason:", rejected.reason)