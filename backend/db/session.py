import os
import certifi

from psycopg import pq
from psycopg_pool import AsyncConnectionPool
from aurora_dsql_psycopg import DSQLAsyncConnection

from core.logger import logger


class DSQLDatabase:
    def __init__(self, cluster_user, cluster_endpoint):
        self.cluster_user = cluster_user
        self.cluster_endpoint = cluster_endpoint

        self.pool: AsyncConnectionPool | None = None

    def _get_connection_params(self) -> dict:
        ssl_cert_path = certifi.where()

        if not os.path.isfile(ssl_cert_path):
            raise FileNotFoundError(
                f"SSL certificate file not found: {ssl_cert_path}"
            )

        conn_params = {
            "user": self.cluster_user,
            "host": self.cluster_endpoint,
            "sslmode": "verify-full",
            "sslrootcert": ssl_cert_path,
        }

        if pq.version() >= 170000:
            conn_params["sslnegotiation"] = "direct"

        return conn_params

    # async def _configure_connection(self, conn):
    #     schema = (
    #         "public"
    #         if self.cluster_user == "admin"
    #         else "myschema"
    #     )
    #
    #     async with conn.cursor() as cur:
    #         await cur.execute(f"SET search_path = {schema};")
    #         await conn.commit()

    async def init(self):
        logger.info("Initializing AWS DSQL connection pool...")

        self.pool = AsyncConnectionPool(
            "",
            connection_class=DSQLAsyncConnection,
            kwargs=self._get_connection_params,
            min_size=2,
            max_size=20,
            max_lifetime=300,
            max_idle=120,
            check=AsyncConnectionPool.check_connection,
            open=False,
        )
        await self.pool.open()
        await self.pool.wait()


        logger.info("AWS DSQL connection pool initialized")

        statements = [
            """
            CREATE TABLE IF NOT EXISTS available_slots (
                id UUID PRIMARY KEY,
                day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                max_capacity INT NOT NULL DEFAULT 1 CHECK (max_capacity >= 1),
                UNIQUE (day_of_week, start_time)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS appointments (
                id UUID PRIMARY KEY,
                customer_name VARCHAR(100) NOT NULL,
                customer_phone VARCHAR(20) NOT NULL,
                customer_email VARCHAR(255) NOT NULL,
                slot_date DATE NOT NULL,
                start_time TIME NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
                    CHECK (status IN ('PENDING', 'CONFIRMED', 'CANCELED'))
            )
            """,
            """
            CREATE INDEX ASYNC IF NOT EXISTS idx_appointments_date_time
            ON appointments(slot_date, start_time)
            """,
            """
            CREATE INDEX ASYNC IF NOT EXISTS idx_slots_day
            ON available_slots(day_of_week)
            """
        ]
        logger.info("Checking and creating database tables if needed...")

        try:
            async with self.pool.connection() as conn:
                await conn.set_autocommit(True)
                async with conn.cursor() as cur:
                    for create_table_query in statements:
                        await cur.execute(create_table_query)
            logger.info("Database tables initialized successfully.")
        except Exception as e:
            logger.error(f"failed create tables error: {e}")

    async def close(self):
        if self.pool:
            logger.info("Closing AWS DSQL connection pool...")

            await self.pool.close()
            self.pool = None

    async def connection(self):
        """Provide one active database connection for the duration of a request."""
        if self.pool is None:
            raise RuntimeError("Database pool is not initialized")

        # pool.connection() is an async context manager. FastAPI understands an
        # async generator dependency and runs this cleanup after the request.
        async with self.pool.connection() as conn:
            yield conn
