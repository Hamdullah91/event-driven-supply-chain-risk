from src.nlp.entity_resolution.integration import (
    get_resolution_stats,
    resolve_extracted_companies,
)


company_names = [
    "TSMC",
    "Taiwan Semiconductor Manufacturing Co.",
    "NVIDIA Corp.",
    "Intel Corporation",
    "Boeing",
    "Unknown Supplier XYZ",
]

results = resolve_extracted_companies(company_names)

for result in results:
    print(
        result.original_name,
        "->",
        result.canonical_name,
        "|",
        result.resolution_method,
        "|",
        result.confidence,
    )

print()
print(get_resolution_stats(results))