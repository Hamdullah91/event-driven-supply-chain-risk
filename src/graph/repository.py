"""
Repository for persisting supply chain domain objects in Neo4j.
"""

import json

from src.events.models import SupplyChainEvent
from src.events.serialization import event_to_dict
from src.graph.connection import Neo4jConnection
from src.graph.contracts import validate_coordinates


class GraphRepository:
    """Handles persistence of domain objects in the Neo4j graph."""

    def __init__(self, connection: Neo4jConnection) -> None:
        self.connection = connection

    def save_event(self, event: SupplyChainEvent) -> None:
        event_data = event_to_dict(event)
        query = """
        MERGE (event:Event {event_id: $event_id})
        ON CREATE SET event.created_at = $created_at
        SET event.event_type = $event_type,
            event.source = $source,
            event.timestamp = $timestamp,
            event.entity_id = $entity_id,
            event.severity = $severity,
            event.payload = $payload
        """
        with self.connection.driver.session() as session:
            session.run(query, event_id=event_data["event_id"], event_type=event_data["event_type"], source=event_data["source"], timestamp=event_data["timestamp"], entity_id=event_data["entity_id"], severity=event_data["severity"], payload=json.dumps(event_data["payload"]), created_at=event_data["created_at"]).consume()

    def seed_companies(self, companies: list[dict]) -> None:
        query = """
        UNWIND $companies AS company
        MERGE (c:Company {company_id: company.company_id})
        SET c.name = company.name, c.legal_name = company.legal_name,
            c.entity_type = company.entity_type, c.seed_source = company.seed_source
        WITH c, company
        MATCH (i:Industry {industry_id: company.industry_id})
        MERGE (c)-[:OPERATES_IN]->(i)
        """
        with self.connection.driver.session() as session:
            session.run(query, companies=companies).consume()

    def seed_facilities(self, facilities: list[dict]) -> None:
        query = """
        UNWIND $facilities AS facility
        MERGE (f:Facility {facility_id: facility.facility_id})
        SET f.name = facility.name, f.facility_type = facility.facility_type,
            f.city = facility.city, f.region = facility.region,
            f.country = facility.country, f.source_type = facility.source_type,
            f.verification_status = facility.verification_status
        WITH f, facility
        MATCH (c:Company {company_id: facility.company_id})
        MATCH (l:Location {location_id: facility.location_id})
        MERGE (c)-[:OPERATES]->(f)
        MERGE (f)-[:LOCATED_IN]->(l)
        """
        with self.connection.driver.session() as session:
            session.run(query, facilities=facilities).consume()

    def seed_countries(self, countries: list[dict]) -> None:
        query = """
        UNWIND $countries AS country
        MERGE (c:Country {country_id: country.country_id})
        SET c.name = country.name, c.iso_code = country.iso_code
        """
        with self.connection.driver.session() as session:
            session.run(query, countries=countries).consume()

    def seed_locations(self, locations: list[dict]) -> None:
        """Persist Location nodes, verified coordinates, and Country links."""
        for location in locations:
            validate_coordinates(location.get("latitude"), location.get("longitude"))
        query = """
        UNWIND $locations AS location
        MERGE (l:Location {location_id: location.location_id})
        SET l.city = location.city,
            l.region = location.region,
            l.latitude = location.latitude,
            l.longitude = location.longitude,
            l.coordinate_source = location.coordinate_source
        WITH l, location
        MATCH (c:Country {country_id: location.country_id})
        MERGE (l)-[:LOCATED_IN]->(c)
        """
        with self.connection.driver.session() as session:
            session.run(query, locations=locations).consume()

    def seed_materials(self, materials: list[dict]) -> None:
        query = """
        UNWIND $materials AS material
        MERGE (m:Material {material_id: material.material_id})
        SET m.name = material.name, m.category = material.category
        """
        with self.connection.driver.session() as session:
            session.run(query, materials=materials).consume()

    def seed_products(self, products: list[dict]) -> None:
        query = """
        UNWIND $products AS product
        MERGE (p:Product {product_id: product.product_id})
        SET p.name = product.name, p.category = product.category
        """
        with self.connection.driver.session() as session:
            session.run(query, products=products).consume()

    def seed_technologies(self, technologies: list[dict]) -> None:
        query = """
        UNWIND $technologies AS technology
        MERGE (t:Technology {technology_id: technology.technology_id})
        SET t.name = technology.name, t.category = technology.category
        """
        with self.connection.driver.session() as session:
            session.run(query, technologies=technologies).consume()

    def seed_industries(self, industries: list[dict]) -> None:
        query = """
        UNWIND $industries AS industry
        MERGE (i:Industry {industry_id: industry.industry_id})
        SET i.name = industry.name
        """
        with self.connection.driver.session() as session:
            session.run(query, industries=industries).consume()
