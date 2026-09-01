import json
from pathlib import Path

from src.graph.connection import Neo4jConnection
from src.graph.repository import GraphRepository


def load_json(path: str) -> list[dict]:
    """
    Load seed data from a JSON file.
    """
    file_path = Path(path)

    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main() -> None:
    """
    Seed baseline supply chain data into Neo4j.
    """
    countries = load_json("data/seed/countries.json")
    locations = load_json("data/seed/locations.json")
    companies = load_json("data/seed/companies.json")
    facilities = load_json("data/seed/facilities.json")
    materials = load_json("data/seed/materials.json")
    products = load_json("data/seed/products.json")
    technologies = load_json("data/seed/technologies.json")
    company_products = load_json("data/seed/company_products.json")
    company_technologies = load_json("data/seed/company_technologies.json")
    company_materials = load_json("data/seed/company_materials.json")
    company_dependencies = load_json("data/seed/company_dependencies.json")

    connection = Neo4jConnection()
    repository = GraphRepository(connection)

    repository.seed_countries(countries)
    repository.seed_locations(locations)
    repository.seed_companies(companies)
    repository.seed_facilities(facilities)
    repository.seed_materials(materials)
    repository.seed_products(products)
    repository.seed_technologies(technologies)
    repository.seed_company_products(company_products)
    repository.seed_company_technologies(company_technologies)
    repository.seed_company_materials(company_materials)
    repository.seed_company_dependencies(company_dependencies)
    connection.close()

    print(f"Seeded {len(countries)} countries successfully")
    print(f"Seeded {len(locations)} locations successfully")
    print(f"Seeded {len(companies)} companies successfully")
    print(f"Seeded {len(facilities)} facilities successfully")
    print(f"Seeded {len(materials)} materials successfully")
    print(f"Seeded {len(products)} products successfully")
    print(f"Seeded {len(technologies)} technologies successfully")
    print(f"Seeded {len(company_products)} company-product relationships successfully")
    print(f"Seeded {len(company_technologies)} company-technology relationships successfully")
    print(f"Seeded {len(company_materials)} company-material relationships successfully")
    print(f"Seeded {len(company_dependencies)} company-dependency relationships successfully")
if __name__ == "__main__":
    main()