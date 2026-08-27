
import os

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase


load_dotenv()


class Neo4jConnection:
    """Manages the application's connection to Neo4j."""

    def __init__(self) -> None:
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")

        if not self.uri:
            raise ValueError("NEO4J_URI is not configured.")

        if not self.username:
            raise ValueError("NEO4J_USERNAME is not configured.")

        if not self.password:
            raise ValueError("NEO4J_PASSWORD is not configured.")

        self.driver: Driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password),
        )

    def verify_connection(self) -> bool:
        """Verify that the Neo4j server is reachable."""
        self.driver.verify_connectivity()
        return True

    def close(self) -> None:
        """Close the Neo4j driver."""
        self.driver.close()
