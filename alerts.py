"""
Handles logging from plugins and other events.
Stores entries in a SQLite database.
Entries are temporary, and are deleted after 24 hours.

Usage:
    This module is not meant to be run directly.
"""


import sqlite3
import logging


class AlertLogger:
    '''
    AlertLogger class
    Handles logging from plugins and other events.
    Stores entries in a SQLite database.

    Methods:
        __init__(): Initializes the AlertLogger with a database path.
        __len__(): Returns the number of recent alerts.
        __iter__(): Returns an iterator over the recent alerts.
        __getitem__(index): Returns a specific alert by index.
        __repr__(): Returns a string representation of the AlertLogger.
        __contains__(message): Checks if an alert message exists.
        init_db(): Initializes the database.
        log_alert(source, message): Logs an alert to the database.
        purge_old_alerts(): Purges alerts older than 24 hours.
        get_recent_alerts(): Retrieves recent alerts from the database.
    '''

    def __init__(
        self,
        db_path='alerts.db'
    ) -> None:
        '''
        Initializes the AlertLogger with a database path.

        Parameters:
            db_path (str): The path to the SQLite database file.

        Returns:
            None
        '''

        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.c = self.conn.cursor()
        self.init_db()

    def __len__(
        self
    ) -> int:
        '''
        Returns the number of recent alerts.

        Parameters:
            None

        Returns:
            int: The number of recent alerts.
        '''

        return len(self.get_recent_alerts())

    def __iter__(
        self
    ) -> iter:
        '''
        Returns an iterator over the recent alerts.

        Parameters:
            None

        Returns:
            iter: An iterator over the recent alerts.
        '''

        return iter(self.get_recent_alerts())

    def __getitem__(
        self,
        index
    ) -> tuple:
        '''
        Returns a specific alert by index.

        Parameters:
            index (int): The index of the alert to retrieve.

        Returns:
            tuple: A tuple containing the timestamp,
                source, and message of the alert.
        '''

        return self.get_recent_alerts()[index]

    def __repr__(
        self
    ) -> str:
        '''
        Returns a string representation of the AlertLogger.

        Parameters:
            None

        Returns:
            str: A string representation of the AlertLogger.
        '''

        return f"<AlertLogger db_path='{self.db_path}'>"

    def __contains__(
        self,
        message
    ) -> bool:
        '''
        Checks if a specific alert message exists in the recent alerts.

        Parameters:
            message (str): The alert message to check for.

        Returns:
            bool: True if the message exists in recent alerts, False otherwise.
        '''

        return any(alert[2] == message for alert in self.get_recent_alerts())

    def init_db(
        self
    ) -> None:
        '''
        Initializes the database.
        Creates the alerts table if it doesn't exist.

        Parameters:
            None

        Returns:
            None
        '''

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
        '''
        Logs an alert to the database.

        Parameters:
            source (str): The source of the alert (e.g., plugin name).
            group (str): The group of the alert (e.g., plugin).
            category (str): The category of the alert (e.g., plugin).
            alert (str): The alert type (e.g., event, error).
            severity (str): The severity level of the alert
            timestamp (str): The timestamp of the alert.
            message (str): The alert message.

        Returns:
            None
        '''

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
        '''
        Purges alerts older than 24 hours from the database.

        Parameters:
            limit (int): The maximum number of alerts to keep.
                Default is 10000.

        Returns:
            None
        '''

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
        self
    ) -> list:
        '''
        Retrieves recent alerts from the database.

        Parameters:
            None

        Returns:
            list: A list of tuples containing
                the timestamp, source, and message of each alert.
        '''

        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
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
                ORDER BY timestamp DESC
            """)
            return c.fetchall()


if __name__ == "__main__":
    print("This module is not meant to be run directly.")
    print("Please run the main.py module instead.")
