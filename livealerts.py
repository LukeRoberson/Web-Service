"""
Module: livealerts.py

Handles logging from plugins and other services. These logs are displayed
    on the /alerts page.

Log entries are stored in an SQLite database. This is intended to be only
    recent alerts. Long-term alerts should be stored in a more permanent
    database or syslog server.
The SQLite database is created when the container starts. It is not saved
    when the container stops.

Log purging (to keep the database size manageable):
    Old alerts are purged after 24 hours.
    A maximum of 10,000 alerts are kept in the database.

Classes:
    LiveAlerts:
        Class to manage live alerts. Includes creating the database, logging
        alerts, purging old alerts, and retrieving recent alerts.

Dependencies:
    sqlite3: For database operations.
    logging: For logging messages.
"""


import sqlite3
import logging
from typing import (
    List,
    Tuple,
    Iterable,
    Optional
)


class LiveAlerts:
    """
    Handles logging from plugins and other events.
    Stores entries in a SQLite database.

    Arguments:
        db_path (str): The path to the SQLite database file.
    """

    def __init__(
        self,
        db_path='alerts.db'
    ) -> None:
        """
        Initializes the SQLite database.

        Args:
            db_path (str): The path to the SQLite database file.

        Returns:
            None
        """

        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.c = self.conn.cursor()
        self.init_db()

    def __len__(
        self
    ) -> int:
        """
        Returns the number of recent alerts.

        Args:
            None

        Returns:
            int: The number of recent alerts.
        """

        return len(self.get_recent_alerts())

    def __iter__(
        self
    ) -> Iterable:
        """
        Returns an iterator over the recent alerts.

        Args:
            None

        Returns:
            iter: An iterator over the recent alerts.
        """

        return iter(self.get_recent_alerts())

    def __getitem__(
        self,
        index: int
    ) -> Tuple:
        """
        Returns a specific alert by index.

        Args:
            index (int): The index of the alert to retrieve.

        Returns:
            tuple: A tuple containing the timestamp,
                source, and message of the alert.
        """

        return self.get_recent_alerts()[index]

    def __repr__(
        self
    ) -> str:
        """
        Returns a string representation of the AlertLogger.

        Args:
            None

        Returns:
            str: A string representation of the AlertLogger.
        """

        return f"<LiveAlerts db_path='{self.db_path}'>"

    def __contains__(
        self,
        message: str
    ) -> bool:
        """
        Checks if a specific alert message exists in the recent alerts.

        Args:
            message (str): The alert message to check for.

        Returns:
            bool: True if the message exists in recent alerts, False otherwise.
        """

        return any(alert[2] == message for alert in self.get_recent_alerts())

    def _build_alerts_query(
        self,
        count: bool = False,
        offset: int = 0,
        limit: Optional[int] = None,
        search: str = '',
        source: str = '',
        group: str = '',
        category: str = '',
        alert: str = '',
        severity: str = ''
    ) -> Tuple[str, List[str]]:
        """
        Builds a SQL query to retrieve or count alerts from the database.
        This method constructs a query based on the provided parameters.
        Used internally by get_recent_alerts and count_alerts.

        Args:
            count (bool): If True, builds a COUNT query.
            offset (int): The number of alerts to skip for pagination.
            limit (int): The maximum number of alerts to retrieve.
            search (str): A search term to filter alerts by message.
            source (str): A source to filter alerts by.
            group (str): A group to filter alerts by.
            category (str): A category to filter alerts by.
            alert (str): An alert type to filter alerts by.
            severity (str): A severity level to filter alerts by.

        Returns:
            tuple:
                str: The SQL query string.
                list: A list of parameters to bind to the query.
        """

        # Base SELECT or COUNT
        if count:
            query = """
                SELECT
                COUNT(*)
                FROM alerts
                WHERE timestamp >= datetime('now', '-24 hours')
            """

        else:
            query = """
                SELECT
                    timestamp,
                    source,
                    "group",
                    category,
                    alert,
                    severity,
                    message
                FROM alerts
                WHERE timestamp >= datetime('now', '-24 hours')
            """
        params = []

        # Add filters
        if search:
            query += " AND message LIKE ?"
            params.append(f"%{search}%")
        if source:
            query += " AND source = ?"
            params.append(source)
        if group:
            query += " AND \"group\" = ?"
            params.append(group)
        if category:
            query += " AND category = ?"
            params.append(category)
        if alert:
            query += " AND alert = ?"
            params.append(alert)
        if severity:
            query += " AND severity = ?"
            params.append(severity)

        # Add ordering and pagination for SELECT
        if not count:
            query += " ORDER BY timestamp DESC"
            if limit is not None:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

        return query, params

    def init_db(
        self
    ) -> None:
        """
        Creates the alerts table if it doesn't exist.

        Args:
            None

        Returns:
            None
        """

        self.c.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                source TEXT,
                "group" TEXT,
                category TEXT,
                alert TEXT,
                severity TEXT,
                message TEXT
            )
        """)
        self.conn.commit()
        logging.info("Database initialized at %s", self.db_path)

    def log_alert(
        self,
        source: str,
        group: str,
        category: str,
        alert: str,
        severity: str,
        timestamp: str,
        message: str,
    ) -> None:
        """
        Logs an alert to the database.

        Args:
            source (str): The source of the alert (e.g., plugin name).
            group (str): The group of the alert (e.g., plugin).
            category (str): The category of the alert (e.g., plugin).
            alert (str): The alert type (e.g., event, error).
            severity (str): The severity level of the alert
            timestamp (str): The timestamp of the alert.
            message (str): The alert message.

        Returns:
            None
        """

        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO alerts (
                    timestamp,
                    source,
                    "group",
                    category,
                    alert,
                    severity,
                    message
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    source,
                    group,
                    category,
                    alert,
                    severity,
                    message
                )
            )
            conn.commit()

    def purge_old_alerts(
        self,
        limit: int = 10000,
    ) -> None:
        """
        Purges alerts older than 24 hours from the database.

        Parameters:
            limit (int): The maximum number of alerts to keep.
                Default is 10000.

        Returns:
            None
        """

        # Purge old alerts older than 24 hours
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                DELETE FROM alerts
                WHERE timestamp < datetime('now', '-24 hours')
            """)
            conn.commit()

        # Purge old alerts if the limit is reached
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                DELETE FROM alerts
                WHERE id NOT IN (
                    SELECT id FROM alerts
                    ORDER BY timestamp DESC
                    LIMIT ?
                )
            """, (limit,))
            conn.commit()

    def get_recent_alerts(
        self,
        offset: int = 0,
        limit: Optional[int] = None,
        search: str = '',
        source: str = '',
        group: str = '',
        category: str = '',
        alert: str = '',
        severity: str = '',
    ) -> List[Tuple[str, str, str]]:
        """
        Retrieves recent alerts from the database.
        By default, this:
            Retrieves all alerts from the last 24 hours
            Starts from the most recent alert

        Pagination is supported:
            Set a limit to retrieve a specific number of alerts.
            Set an offset to start getting alerts from a specific point.

        Args:
            offset (int): The number of alerts to skip.
                This is useful for pagination.
            limit (int): The maximum number of alerts to retrieve.
            search (str): A search term to filter alerts by message.
                If blank, all alerts are returned.
            source (str): A source to filter alerts by.
            group (str): A group to filter alerts by.
            category (str): A category to filter alerts by.
            alert (str): An alert type to filter alerts by.
            severity (str): A severity level to filter alerts by.

        Returns:
            list: A list of tuples containing
                the timestamp, source, and message of each alert.
        """

        # Build the query with the provided parameters
        query, params = self._build_alerts_query(
            count=False, offset=offset, limit=limit,
            search=search, source=source, group=group,
            category=category, alert=alert, severity=severity
        )

        # Execute the query and fetch results
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(query, params)
            return c.fetchall()

    def count_alerts(
        self,
        search: str = '',
        source: str = '',
        group: str = '',
        category: str = '',
        alert: str = '',
        severity: str = '',
    ) -> int:
        """
        Counts the number of alerts in the database.
        Optionally filters by a search term.

        Parameters:
            search (str): A search term to filter alerts by message.
                If blank, all alerts are counted.
            source (str): A source to filter alerts by.
            group (str): A group to filter alerts by.
            category (str): A category to filter alerts by.
            alert (str): An alert type to filter alerts by.
            severity (str): A severity level to filter alerts by.

        Returns:
            int: The number of alerts matching the criteria.
        """

        # Build the count query with the provided parameters
        query, params = self._build_alerts_query(
            count=True,
            search=search, source=source, group=group,
            category=category, alert=alert, severity=severity
        )

        # Execute the count query and return the result
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(query, params)
            return c.fetchone()[0]


if __name__ == "__main__":
    print("This module is not meant to be run directly.")
    print("Please run the main.py module instead.")
