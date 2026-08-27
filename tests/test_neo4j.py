
from src.graph.connection import Neo4jConnection


def main() -> None:
    connection = Neo4jConnection()

    try:
        connection.verify_connection()

        with connection.driver.session() as session:

            # Create a temporary test node
            create_result = session.run(
                """
                CREATE (company:Company {
                    name: $name,
                    test: true
                })
                RETURN company.name AS name
                """,
                name="Test Semiconductor Corp",
            )

            created_record = create_result.single()

            if created_record is None:
                raise RuntimeError("Neo4j did not return the created node.")

            print(f"Created company: {created_record['name']}")

            # Read the test node back
            read_result = session.run(
                """
                MATCH (company:Company {
                    name: $name,
                    test: true
                })
                RETURN company.name AS name
                """,
                name="Test Semiconductor Corp",
            )

            companies = [record["name"] for record in read_result]

            if "Test Semiconductor Corp" not in companies:
                raise RuntimeError("Test node could not be read from Neo4j.")

            print(f"Companies found: {companies}")

            # Clean up the temporary test node
            session.run(
                """
                MATCH (company:Company {
                    name: $name,
                    test: true
                })
                DELETE company
                """,
                name="Test Semiconductor Corp",
            )

            print("Test data cleaned up.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()