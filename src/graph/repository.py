"""
Repository for persisting supply chain domain objects in Neo4j.
"""

import json

from src.events.models import SupplyChainEvent
from src.events.serialization import event_to_dict
from src.graph.connection import Neo4jConnection


class GraphRepository:
    """Handles persistence of domain objects in the Neo4j graph."""

    def __init__(self, connection: Neo4jConnection) -> None:
        self.connection = connection

    def save_event(self, event: SupplyChainEvent) -> None:
        """
        Persist a SupplyChainEvent as an Event node in Neo4j.
        """

        event_data = event_to_dict(event)

        query = """
        MERGE (event:Event {event_id: $event_id})
        SET
            event.event_type = $event_type,
            event.source = $source,
            event.timestamp = $timestamp,
            event.entity_id = $entity_id,
            event.severity = $severity,
            event.payload = $payload,
            event.created_at = $created_at
        """

        with self.connection.driver.session() as session:
            session.run(
                query,
                event_id=event_data["event_id"],
                event_type=event_data["event_type"],
                source=event_data["source"],
                timestamp=event_data["timestamp"],
                entity_id=event_data["entity_id"],
                severity=event_data["severity"],
                payload=json.dumps(event_data["payload"]),
                created_at=event_data["created_at"],
            )

    def seed_companies(self, companies: list[dict]) -> None:
        """
        Persist seed Company nodes and connect them to Industry nodes.
        """

        query = """
        UNWIND $companies AS company

        MERGE (c:Company {company_id: company.company_id})
        SET
            c.name = company.name,
            c.legal_name = company.legal_name,
            c.entity_type = company.entity_type,
            c.seed_source = company.seed_source

        WITH c, company

        MATCH (i:Industry {industry_id: company.industry_id})

        MERGE (c)-[:OPERATES_IN]->(i)
        """

        with self.connection.driver.session() as session:
            session.run(
                query,
                companies=companies,
            ).consume()

    def seed_facilities(self, facilities: list[dict]) -> None:
        """
        Persist Facility nodes and connect them to Company and Location nodes.
        """

        query = """
        UNWIND $facilities AS facility

        MERGE (f:Facility {facility_id: facility.facility_id})
        SET
            f.name = facility.name,
            f.facility_type = facility.facility_type,
            f.city = facility.city,
            f.region = facility.region,
            f.country = facility.country,
            f.source_type = facility.source_type,
            f.verification_status = facility.verification_status

        WITH f, facility

        MATCH (c:Company {company_id: facility.company_id})
        MATCH (l:Location {location_id: facility.location_id})

        MERGE (c)-[:OPERATES]->(f)
        MERGE (f)-[:LOCATED_IN]->(l)
        """

        with self.connection.driver.session() as session:
            session.run(
                query,
                facilities=facilities,
            ).consume()

    def seed_countries(self, countries: list[dict]) -> None:
        """
        Persist Country nodes in Neo4j.
        """

        query = """
        UNWIND $countries AS country

        MERGE (c:Country {country_id: country.country_id})
        SET
            c.name = country.name,
            c.iso_code = country.iso_code
        """

        with self.connection.driver.session() as session:
            session.run(
                query,
                countries=countries,
            ).consume()


    def seed_locations(self, locations: list[dict]) -> None:
        """
        Persist Location nodes and connect them to Country nodes.
        """

        query = """
        UNWIND $locations AS location

        MERGE (l:Location {location_id: location.location_id})
        SET
            l.city = location.city,
            l.region = location.region

        WITH l, location

        MATCH (c:Country {country_id: location.country_id})

        MERGE (l)-[:LOCATED_IN]->(c)
        """

        with self.connection.driver.session() as session:
            session.run(
                query,
                locations=locations,
            ).consume()

    def seed_materials(self, materials: list[dict]) -> None:
        """
        Persist Material nodes in Neo4j.
        """

        query = """
        UNWIND $materials AS material

        MERGE (m:Material {material_id: material.material_id})
        SET
            m.name = material.name,
            m.category = material.category
        """

        with self.connection.driver.session() as session:
            session.run(
                query,
                materials=materials,
            ).consume()
    def seed_products(self, products: list[dict]) -> None:
        """
        Persist Product nodes in Neo4j.
        """

        query = """
        UNWIND $products AS product

        MERGE (p:Product {product_id: product.product_id})
        SET
            p.name = product.name,
            p.category = product.category
        """

        with self.connection.driver.session() as session:
            session.run(
                query,
                products=products,
            ).consume()
    def seed_technologies(self, technologies: list[dict]) -> None:
        """
        Persist Technology nodes in Neo4j.
        """

        query = """
        UNWIND $technologies AS technology

        MERGE (t:Technology {technology_id: technology.technology_id})
        SET
            t.name = technology.name,
            t.category = technology.category
        """

        with self.connection.driver.session() as session:
            session.run(
                query,
                technologies=technologies,
            ).consume()
    def seed_company_products(self, company_products: list[dict]) -> None:
        """
        Connect Company nodes to Product nodes using PRODUCES relationships.
        """

        query = """
        UNWIND $company_products AS item

        MATCH (c:Company {company_id: item.company_id})
        MATCH (p:Product {product_id: item.product_id})

        MERGE (c)-[r:PRODUCES]->(p)
        SET
            r.source_type = item.source_type,
            r.source_url = item.source_url,
            r.verification_status = item.verification_status,
            r.confidence = item.confidence
        """

        with self.connection.driver.session() as session:
            session.run(
                query,
                company_products=company_products,
            ).consume()
    def seed_company_technologies(
        self,
        company_technologies: list[dict],
    ) -> None:
        """
        Connect Company nodes to Technology nodes using USES relationships.
        """

        query = """
        UNWIND $company_technologies AS item

        MATCH (c:Company {company_id: item.company_id})
        MATCH (t:Technology {technology_id: item.technology_id})

        MERGE (c)-[r:USES]->(t)
        SET
            r.source_type = item.source_type,
            r.source_url = item.source_url,
            r.verification_status = item.verification_status,
            r.confidence = item.confidence
        """

        with self.connection.driver.session() as session:
            session.run(
                query,
                company_technologies=company_technologies,
            ).consume()
    def seed_company_materials(
        self,
        company_materials: list[dict],
    ) -> None:
        """
        Connect Company nodes to Material nodes using USES relationships.
        """

        query = """
        UNWIND $company_materials AS item

        MATCH (c:Company {company_id: item.company_id})
        MATCH (m:Material {material_id: item.material_id})

        MERGE (c)-[r:USES]->(m)
        SET
            r.source_type = item.source_type,
            r.verification_status = item.verification_status,
            r.confidence = item.confidence
        """

        with self.connection.driver.session() as session:
            session.run(
                query,
                company_materials=company_materials,
            ).consume()
    def seed_company_dependencies(
        self,
        company_dependencies: list[dict],
    ) -> None:
        """
        Create verified SUPPLIES relationships and their derived
        DEPENDS_ON inverse relationships between Company nodes.
        """

        query = """
        UNWIND $company_dependencies AS item

        MATCH (supplier:Company {
            company_id: item.supplier_company_id
        })

        MATCH (customer:Company {
            company_id: item.customer_company_id
        })

        MERGE (supplier)-[s:SUPPLIES]->(customer)
        SET
            s.source_type = item.source_type,
            s.source_url = item.source_url,
            s.verification_status = item.verification_status,
            s.confidence = item.confidence

        MERGE (customer)-[d:DEPENDS_ON]->(supplier)
        SET
            d.source_type = "derived_from_verified_supplies",
            d.source_url = item.source_url,
            d.verification_status = item.verification_status,
            d.confidence = item.confidence,
            d.derivation = "inverse_of_SUPPLIES"
        """

        with self.connection.driver.session() as session:
            session.run(
                query,
                company_dependencies=company_dependencies,
            ).consume()