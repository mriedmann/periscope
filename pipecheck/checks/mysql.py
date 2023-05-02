from typing import Optional

import pymysql

from pipecheck.api import CheckResult, Err, Ok, Probe


class MysqlProbe(Probe):
    """Try MySQL Connection to given host and port using given user and password"""

    host: str = ""
    port: int = 3306
    database: Optional[str] = None
    user: str = ""
    password: str = ""
    timeout: int = 5

    def __call__(self) -> CheckResult:
        connection = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            connect_timeout=self.timeout,
            defer_connect=True,
        )
        try:
            connection.connect()
            return Ok(f"MySQL connection successfully established to port {self.port} on {self.host}")
        except Exception as e:
            return Err(f"MySQL connection failed on port {self.port} for {self.host} ({e})")
        finally:
            connection.close()
