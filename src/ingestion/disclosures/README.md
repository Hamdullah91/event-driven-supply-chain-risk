# Multi-Jurisdiction Corporate Disclosure Ingestion

This package generalizes the original SEC-only annual filing pipeline into a
configuration-driven disclosure platform.

## Architectural boundary

Corporate disclosures are **source-specific during discovery/acquisition**,
**format-specific during normalization**, and **source-independent after
normalization**.

```text
Company Registry
      |
Source Router
      |
+-----+--------------------+
|          |               |
SEC      OpenDART     Official IR
|          |               |
+----------+---------------+
           |
       RawArtifact
           |
    Content-addressed
       raw storage
           |
 +---------+---------+---------+
 |         |         |         |
HTML      XML       PDF       JSON
 +---------+---------+---------+
           |
  NormalizedDisclosure
           |
    Document Registry
           |
     Existing NLP
           |
 Entity Resolution
           |
     Validation
           |
       Neo4j
```

## Design rules

1. Adding a company must normally be a registry/configuration change, not a new
   crawler.
2. Adding a regulator means implementing `DisclosureProvider`, then registering
   that provider. NLP and graph code do not change.
3. Provider adapters discover/download only. They do not perform NLP or Neo4j
   writes.
4. HTML/XML/PDF/JSON parsing is format-specific, not provider-specific.
5. Raw artifacts are immutable and content-addressed by SHA-256.
6. A logical corporate report can have multiple source representations. The
   same bytes from a regulator and issuer can share storage while retaining both
   source occurrences/provenance.
7. Neo4j is graph truth, not crawler state. SQLite tracks document identity,
   acquisition state, normalized documents and failures.
8. English disclosures are eligible for the current NLP pipeline. Other
   languages are retained as `NORMALIZED_UNSUPPORTED_LANGUAGE` for future work.
9. Provider failures are isolated. A failed primary source does not stop other
   companies or configured fallback sources.
10. Official/regulatory sources only. The IR provider is intentionally a
    shallow, same-domain crawler rooted at an explicitly configured official
    URL; it is not a general web crawler.

## Registry files

- `data/seed/companies.json`: canonical company identity.
- `data/seed/sec_10k_targets.json`: existing SEC 10-K identities.
- `data/seed/sec_20f_targets.json`: existing SEC 20-F identities.
- `data/seed/disclosure_sources.json`: provider/source definitions.
- `data/seed/disclosure_source_bindings.json`: company-to-provider identities,
  priorities and official discovery URLs.

Provider-specific identifiers do not need to become hard-coded properties on
`Company`. They are represented as namespaced identifiers or source bindings.

## Add company #51 or #500

1. Add the canonical company to `companies.json`.
2. Add one or more verified disclosure bindings/identifiers.
3. Run the coverage audit.
4. Run ingestion.

No central `if company == ...` logic should be added.

## Add a new regulator/provider

Implement:

```python
class NewProvider(DisclosureProvider):
    provider_id = "new_provider"

    def supports(self, company, binding) -> bool:
        ...

    async def discover_documents(self, company, binding, **filters):
        ...

    async def fetch_document(self, document):
        ...
```

Then add the source to `disclosure_sources.json`, register the provider in the
composition root/runner, and add company bindings. Existing normalizers and NLP
remain unchanged unless the regulator introduces a genuinely new file format.

## Storage model

```text
Logical DisclosureDocument
        |
        +-- Representation (SEC HTML)
        |       |
        |       +-- SHA-256 artifact
        |
        +-- Representation (issuer PDF)
                |
                +-- SHA-256 artifact
```

Exact byte duplicates share immutable artifact storage while retaining source
occurrences. URLs are not used as the sole identity because they can change.

## Running

Install/update dependencies:

```powershell
python -m pip install -r requirements.txt
```

Audit baseline route coverage:

```powershell
python scripts/audit_disclosure_coverage.py
```

Ingest one company:

```powershell
python scripts/run_disclosure_ingestion.py --company nvidia
```

Ingest several companies:

```powershell
python scripts/run_disclosure_ingestion.py --company samsung_electronics --company bmw
```

Ingest all configured companies:

```powershell
python scripts/run_disclosure_ingestion.py
```

Add `--graph` only after acquisition/normalization has been verified and Neo4j
is running:

```powershell
python scripts/run_disclosure_ingestion.py --company nvidia --graph
```

Required credentials are configured in `.env`:

- `SEC_USER_AGENT` for selected SEC routes.
- `OPENDART_API_KEY` for OpenDART. A missing/failed OpenDART route does not
  prevent an explicitly configured official IR fallback from being attempted.

## FYP scope boundary

Deliberately excluded from the current implementation:

- Kafka, Spark, Airflow, Kubernetes or distributed workers.
- unrestricted internet crawling.
- OCR infrastructure.
- automatic multilingual relation extraction.
- runtime package/plugin discovery machinery.
- every global regulator.

The provider contract makes EDINET, FCA, HKEX, MOPS and other official systems
future additions without redesigning the pipeline.
