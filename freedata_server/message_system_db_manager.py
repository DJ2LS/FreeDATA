# database_manager.py
import sqlite3

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import scoped_session, sessionmaker
from threading import local
from message_system_db_model import Base, Config, Station, Status, P2PMessage
import structlog
import helpers
import os
import sys
from constants import MESSAGE_SYSTEM_DATABASE_VERSION

class DatabaseManager:
    """Manages database connections and operations.

    This class provides a base for database interactions, handling
    database connections, session management, logging, and common
    database operations such as initialization, repair, and retrieval of
    stations and statuses.
    """
    DATABASE_ENV_VAR = 'FREEDATA_DATABASE'
    DEFAULT_DATABASE_FILE = 'freedata-messages.db'

    def __init__(self, event_manager):
        """Initializes the DatabaseManager.

        Args:
            event_manager (EventManager): The event manager instance.
        """
        self.event_manager = event_manager

        db_file = self.get_database()
        self.engine = create_engine(db_file, echo=False)
        self.thread_local = local()
        self.session_factory = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

        self.logger = structlog.get_logger(type(self).__name__)

    def get_database(self):
        """Retrieves the database file path.

        This method determines the database file path based on the
        environment variable `FREEDATA_DATABASE`. If the variable is set,
        its value is used as the path. Otherwise, it defaults to
        `freedata-messages.db` in the script directory.

        Returns:
            str: The database file path as a SQLAlchemy URL.
        """
        script_directory = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(script_directory)

        if self.DATABASE_ENV_VAR in os.environ:
            #db_path = os.getenv(self.DATABASE_ENV_VAR, os.path.join(script_directory, self.DEFAULT_DATABASE_FILE))
            db_path = os.getenv(self.DATABASE_ENV_VAR)
        else:
            db_path = os.path.join(script_directory, self.DEFAULT_DATABASE_FILE)
        return 'sqlite:///' + db_path

    def initialize_default_values(self):
        """Initializes default values in the database.

        This method adds predefined status values to the database if they
        don't already exist. It ensures that the database has the
        necessary status entries for tracking message states. It handles
        potential database errors and performs rollbacks if necessary.
        """
        session = self.get_thread_scoped_session()
        try:
            statuses = [
                "transmitting",
                "transmitted",
                "received",
                "failed",
                "failed_checksum",
                "aborted",
                "queued"
            ]

            # Add default statuses if they don't exist
            for status_name in statuses:
                existing_status = session.query(Status).filter_by(name=status_name).first()
                if not existing_status:
                    new_status = Status(name=status_name)
                    session.add(new_status)

            session.commit()
            self.log("Initialized database")
        except Exception as e:
            session.rollback()
            self.log(f"An error occurred while initializing default values: {e}", isWarning=True)
        finally:
            session.remove()

    def database_repair_and_cleanup(self):
        """Repairs and cleans up the database.

        This method performs several database maintenance tasks:
        1. Updates messages with "transmitting" status to "failed" if the
           FreeDATA server was interrupted during transmission.
        2. Vacuums the database to reclaim unused space.
        3. Reindexes the database to improve query performance.
        4. Performs an integrity check to ensure database consistency.
        It handles potential errors during these operations and logs
        appropriate messages.
        """
        session = self.get_thread_scoped_session()
        try:

            # Fetch the 'failed' status ID
            failed_status = session.query(Status).filter_by(name="failed").first()
            if not failed_status:
                raise ValueError("Failed status not found in the database")

            # Fetch the 'transmitting' status ID
            transmitting_status = session.query(Status).filter_by(name="transmitting").first()
            if transmitting_status:
                # Check if any messages have the status "transmitting" and update them to "failed"
                messages_to_update = session.query(P2PMessage).filter_by(status_id=transmitting_status.id).all()
                for message in messages_to_update:
                    message.status_id = failed_status.id

                session.commit()
                len_repaired_message = len(messages_to_update)
                if len_repaired_message > 0:
                    self.log(f"Repaired {len_repaired_message} messages ('transmitting' to 'failed')")

            # Vacuum the database to reclaim space
            session.execute(text("VACUUM"))
            self.log("Database vacuumed successfully")

            # Reindex all tables to improve query performance
            session.execute(text("REINDEX"))
            self.log("Database reindexed successfully")

            # Perform an integrity check on the database
            result = session.execute(text("PRAGMA integrity_check")).fetchone()
            if result[0] == 'ok':
                self.log("Database integrity check passed")
            else:
                self.log("Database integrity check failed", isWarning=True)

        except Exception as e:
            session.rollback()
            self.log(f"An error occurred while checking databse: {e}", isWarning=True)
        finally:
            session.remove()

    def log(self, message, isWarning=False):
        """Logs a message with appropriate log level.

        This method logs the given message using either `self.logger.warn`
        if isWarning is True, or `self.logger.info` otherwise. It
        prepends the class name to the message for context.

        Args:
            message (str): The message to log.
            isWarning (bool, optional): Whether to log as a warning. Defaults to False.
        """
        msg = f"[{type(self).__name__}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def get_thread_scoped_session(self):
        """Retrieves a thread-scoped database session.

        This method returns a database session that is scoped to the
        current thread. If no session exists for the current thread, it
        creates a new one. This ensures that each thread uses its own
        session, preventing conflicts and data corruption.

        Returns:
            scoped_session: The thread-scoped database session.
        """
        if not hasattr(self.thread_local, "session"):
            self.thread_local.session = scoped_session(self.session_factory)
        return self.thread_local.session

    def get_or_create_station(self, callsign, session=None):
        """Retrieves or creates a station record.

        This method retrieves a station record from the database based on
        the given callsign. If the station doesn't exist, it creates a
        new record with the callsign and its CRC checksum. It handles
        database sessions and transactions appropriately, committing
        changes only if it created the session.

        Args:
            callsign (str): The callsign of the station.
            session (scoped_session, optional): An existing database session.
                Defaults to None.

        Returns:
            Station or None: The Station object if found or created, None if an error occurred.
        """
        own_session = False
        if not session:
            session = self.get_thread_scoped_session()
            own_session = True

        try:
            station = session.query(Station).filter_by(callsign=callsign).first()
            if not station:
                self.log(f"Updating station list with {callsign}")
                station = Station(callsign=callsign, checksum=helpers.get_crc_24(callsign).hex())
                session.add(station)
                session.flush()

            if own_session:
                session.commit()  # Only commit if we created the session

            return station

        except Exception as e:
            self.log(f"An error occurred while getting or creating station {callsign}: {e}", isWarning=True)
            if own_session:
                session.rollback()
            return None  # Indicate failure

        finally:
            if own_session:
                session.remove()

    def get_callsign_by_checksum(self, checksum):
        """Retrieves a callsign by its checksum.

        This method searches for a station in the database matching the
        provided checksum and returns the corresponding callsign if found.
        It logs messages indicating success or failure and handles
        potential database errors.

        Args:
            checksum (str): The checksum to search for.

        Returns:
            str or None: The callsign if found, None otherwise.
        """
        session = self.get_thread_scoped_session()
        try:
            station = session.query(Station).filter_by(checksum=checksum).first()
            if station:
                self.log(f"Found callsign [{station.callsign}] for checksum [{station.checksum}]")
                return station.callsign
            else:
                self.log(f"No callsign found for [{checksum}]")
                return None
        except Exception as e:
            self.log(f"Error fetching callsign for checksum {checksum}: {e}", isWarning=True)
            return None  # Or handle the error as needed
        finally:
            session.remove()

    def get_or_create_status(self, session, status_name):
        """Retrieves or creates a status record.

        This method retrieves a status record from the database based on
        the given status name. If the status doesn't exist, it creates a
        new record. It uses the provided session to interact with the
        database and flushes the session to ensure the new status ID is
        available immediately.

        Args:
            session (scoped_session): The database session object.
            status_name (str): The name of the status.

        Returns:
            Status: The Status object, either retrieved or newly created.
        """
        status = session.query(Status).filter_by(name=status_name).first()
        if not status:
            status = Status(name=status_name)
            session.add(status)
            session.flush()  # To get the ID immediately
        return status


    def check_database_version(self):
        """Updates the database schema to the expected version.

            This method is called by `check_database_version` if the current
            schema version is older than the expected version. It performs
            the necessary schema updates based on the current and expected
            versions. Currently, it only logs a message indicating that
            schema updates are not yet implemented. It takes the current and
            expected versions as arguments, but doesn't use them yet.

            Args:
            current_version (int): The current database schema version.
            expected_version (int): The expected database schema version.
        """
        session = self.get_thread_scoped_session()
        try:
            config = session.query(Config).filter_by(db_variable='database_version').first()
            if config is None:
                config = Config(db_variable='database_version', db_version="0")
                session.add(config)
                session.commit()
                self.log("No database version found. Assuming version 0 and storing it.")

            current_version = int(config.db_version)
            expected_version = int(MESSAGE_SYSTEM_DATABASE_VERSION)

            if current_version < expected_version:
                self.log(
                    f"Database schema outdated (current: {current_version}, expected: {expected_version}). Updating schema...")
                self.update_database_schema()
                config.db_version = str(expected_version)
                session.commit()
                self.log("Database schema updated successfully.")
            elif current_version > expected_version:
                self.log("Database version is newer than the expected version. Manual intervention might be required.",
                         isWarning=True)
            else:
                self.log("Database schema is up-to-date.")
        except Exception as e:
            session.rollback()
            self.log(f"Database version check failed: {e}", isWarning=True)
        finally:
            session.remove()

    def update_database_schema(self):
        """Updates the database schema to the latest version.

        This method updates both tables and columns within the database
        schema. It checks for and adds any missing tables or columns
        defined in the model. It logs the progress and results of the
        schema update.

        Returns:
            bool: True if the schema update was completely successful,
            False otherwise.
        """
        self.log("Starting schema update...")
        tables_success = self.update_tables_schema()
        columns_success = self.update_columns_schema()

        if tables_success and columns_success:
            self.log("Database schema update completed successfully.")
            return True
        else:
            self.log("Database schema update completed with errors.", isWarning=True)
            return False

    def update_tables_schema(self):
        """Updates the database schema by adding new tables.

        This method checks for any new tables defined in the data model
        (Base.metadata) that are not present in the database. If new
        tables are found, it creates them in the database. It logs the
        names of the tables being added and any errors encountered during
        the process.

        Returns:
            bool: True if the table update was successful, False otherwise.
        """
        self.log("Checking for new tables to add to the schema.")
        success = True
        inspector = inspect(self.engine)
        existing_tables = inspector.get_table_names()

        new_tables = [table for table in Base.metadata.sorted_tables if table.name not in existing_tables]

        if new_tables:
            table_names = ", ".join(table.name for table in new_tables)
            self.log(f"New tables to be added: {table_names}")
            try:
                Base.metadata.create_all(self.engine, tables=new_tables)
                self.log("New tables have been added successfully.")
            except Exception as e:
                self.log(f"Error while adding new tables: {e}", isWarning=True)
                success = False
        else:
            self.log("No new tables to add.")
        return success

    def update_columns_schema(self):
        """Updates the database schema by adding missing columns.

        This method checks for any missing columns in existing tables by
        comparing the database schema with the defined models. If missing
        columns are found, it adds them to the respective tables using
        ALTER TABLE statements. It handles different column types,
        nullability, and default values. It logs the DDL statements and
        any errors encountered during the process.

        Returns:
            bool: True if the column update was successful, False otherwise.
        """

        self.log("Checking for missing columns in existing tables.")
        success = True
        inspector = inspect(self.engine)
        existing_tables = inspector.get_table_names()

        for table in Base.metadata.sorted_tables:
            if table.name in existing_tables:
                existing_columns_info = inspector.get_columns(table.name)
                existing_column_names = {col["name"] for col in existing_columns_info}

                for column in table.columns:
                    if column.name not in existing_column_names:
                        col_name = column.name
                        col_type = column.type.compile(dialect=self.engine.dialect)
                        nullable_clause = "" if column.nullable else "NOT NULL"
                        default_clause = ""
                        if column.default is not None and hasattr(column.default, "arg"):
                            default_value = column.default.arg
                            if isinstance(default_value, str):
                                default_clause = f" DEFAULT '{default_value}'"
                            else:
                                default_clause = f" DEFAULT {default_value}"

                        ddl = (
                            f"ALTER TABLE {table.name} ADD COLUMN {col_name} {col_type} "
                            f"{nullable_clause}{default_clause}"
                        )
                        ddl = " ".join(ddl.split())
                        self.log(f"Adding missing column with DDL: {ddl}")
                        try:
                            with self.engine.connect() as conn:
                                conn.execute(text(ddl))
                            self.log(f"Column '{col_name}' added to table '{table.name}'.")
                        except Exception as e:
                            self.log(f"Failed to add column '{col_name}' to table '{table.name}': {e}", isWarning=True)
                            success = False
        return success
