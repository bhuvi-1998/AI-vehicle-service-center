from backend.app.database.database import get_connection

MIGRATIONS = [
    (
        "vehicles",
        "vehicle_type",
        """
        ALTER TABLE vehicles
        ADD COLUMN vehicle_type VARCHAR(20)
        NOT NULL DEFAULT 'Car'
        AFTER customer_id
        """
    ),
    (
        "services",
        "vehicle_type",
        """
        ALTER TABLE services
        ADD COLUMN vehicle_type VARCHAR(20)
        NOT NULL DEFAULT 'Car'
        AFTER description
        """
    ),
    (
        "technicians",
        "vehicle_type",
        """
        ALTER TABLE technicians
        ADD COLUMN vehicle_type VARCHAR(20)
        NOT NULL DEFAULT 'All'
        AFTER specialization
        """
    ),
    (
        "parts",
        "vehicle_type",
        """
        ALTER TABLE parts
        ADD COLUMN vehicle_type VARCHAR(20)
        NOT NULL DEFAULT 'All'
        AFTER part_name
        """
    ),
]


def main():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            for table, column, sql in MIGRATIONS:
                cursor.execute(
                    """
                    SELECT COUNT(*) AS column_count
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = %s
                      AND COLUMN_NAME = %s
                    """,
                    (table, column)
                )

                result = cursor.fetchone()

                if result["column_count"] > 0:
                    print(f"Already exists: {table}.{column}")
                    continue

                cursor.execute(sql)
                print(f"Added: {table}.{column}")

        connection.commit()
        print("\nMigration completed successfully.")

    except Exception as error:
        connection.rollback()
        print(f"\nMigration failed: {error}")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
