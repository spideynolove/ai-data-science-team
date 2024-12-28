import logging
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from config import settings

class PostgreSQLClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connection = psycopg2.connect(
            dsn=settings.POSTGRES_URI,
            cursor_factory=RealDictCursor
        )
        self.cursor = self.connection.cursor()

    async def execute_query(self, query: str, params: tuple = None) -> list:
        """Execute a SQL query and return results"""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            self.logger.error(f"PostgreSQL query failed: {str(e)}")
            return []

    async def insert_record(self, table: str, data: dict) -> bool:
        """Insert a record into a table"""
        try:
            columns = sql.SQL(',').join(map(sql.Identifier, data.keys()))
            values = sql.SQL(',').join(map(sql.Literal, data.values()))
            query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table),
                columns,
                values
            )
            self.cursor.execute(query)
            self.connection.commit()
            return True
        except psycopg2.Error as e:
            self.logger.error(f"PostgreSQL insert failed: {str(e)}")
            self.connection.rollback()
            return False

    async def update_record(self, table: str, data: dict, condition: str) -> bool:
        """Update records in a table"""
        try:
            set_clause = sql.SQL(',').join(
                sql.SQL("{} = {}").format(
                    sql.Identifier(k), sql.Literal(v)
                ) for k, v in data.items()
            )
            query = sql.SQL("UPDATE {} SET {} WHERE {}").format(
                sql.Identifier(table),
                set_clause,
                sql.SQL(condition)
            )
            self.cursor.execute(query)
            self.connection.commit()
            return True
        except psycopg2.Error as e:
            self.logger.error(f"PostgreSQL update failed: {str(e)}")
            self.connection.rollback()
            return False

    async def delete_record(self, table: str, condition: str) -> bool:
        """Delete records from a table"""
        try:
            query = sql.SQL("DELETE FROM {} WHERE {}").format(
                sql.Identifier(table),
                sql.SQL(condition)
            )
            self.cursor.execute(query)
            self.connection.commit()
            return True
        except psycopg2.Error as e:
            self.logger.error(f"PostgreSQL delete failed: {str(e)}")
            self.connection.rollback()
            return False

    async def close(self):
        """Close PostgreSQL connection"""
        try:
            self.cursor.close()
            self.connection.close()
            return True
        except psycopg2.Error as e:
            self.logger.error(f"Failed to close PostgreSQL connection: {str(e)}")
            return False
