from src.nlp.validation import (
    RelationshipCandidate,
    RelationshipValidator,
)


validator = RelationshipValidator()


valid_candidate = RelationshipCandidate(
    subject="NVIDIA",
    subject_type="Company",
    relationship="USES",
    object="Silicon",
    object_type="Material",
)

invalid_candidate = RelationshipCandidate(
    subject="Silicon",
    subject_type="Material",
    relationship="SUPPLIES",
    object="NVIDIA",
    object_type="Company",
)


print("VALID TEST")
print(validator.validate(valid_candidate))

print()

print("INVALID TEST")
print(validator.validate(invalid_candidate))