"""
Nested transactions script using SQLAlchemy.
"""

from sqlalchemy import create_engine, text

db_url = "postgresql+psycopg2://postgres@/db55"
engine = create_engine(db_url, echo=False, future=True)
conn = engine.connect()


class BlockError(Exception):
    """Exception that wraps a failed block with its name and original exception."""
    
    def __init__(self, block_name, original_exception):
        self.block_name = block_name
        self.original_exception = original_exception
        super().__init__(f"Block '{block_name}' failed: {original_exception}")


def exec_sql(conn, sql_string):
    """Execute a SQL statement via the connection."""
    conn.execute(text(sql_string))

def run_block(conn, block_name, work):
    """
    Execute a work function within a savepoint.
    If it fails, catch the exception and raise BlockError with block name.
    """
    try:
        with conn.begin_nested():  # Savepoint starts
            work(conn)             # Execute the work function
        # Success: savepoint released
    except Exception as e:
        # Failure: savepoint rolled back automatically, wrap and re-raise
        raise BlockError(block_name, e)

def drop_tables_work(conn):
    """Drop tables in correct dependency order to respect foreign keys."""
    exec_sql(conn, "DROP TABLE IF EXISTS rps.tbl_rounds")
    exec_sql(conn, "DROP TABLE IF EXISTS rps.tbl_games")
    exec_sql(conn, "DROP TABLE IF EXISTS rps.tbl_players")
    exec_sql(conn, "DROP TABLE IF EXISTS rps.tbl_errata")

def create_players_work(conn):
    """Create the players table."""
    exec_sql(conn, """
        CREATE TABLE rps.tbl_players (
            fld_p_id_pk CHAR(16) PRIMARY KEY,
            fld_p_doc TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

def create_games_work(conn):
    """Create the games table with foreign key constraints to players."""
    exec_sql(conn, """
        CREATE TABLE rps.tbl_games (
            fld_g_id_pk INTEGER PRIMARY KEY,
            fld_g_p1_id_fk CHAR(16) NOT NULL,
            fld_g_p2_id_fk CHAR(16) NOT NULL,
            fld_g_doc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fld_g_p1_id_fk) REFERENCES rps.tbl_players(fld_p_id_pk),
            FOREIGN KEY (fld_g_p2_id_fk) REFERENCES rps.tbl_players(fld_p_id_pk),
            UNIQUE(fld_g_p1_id_fk, fld_g_p2_id_fk),
            CHECK (fld_g_p1_id_fk < fld_g_p2_id_fk)
        )
    """)


def create_rounds_work(conn):
    """Create the rounds table with foreign key to games and unique constraint."""
    exec_sql(conn, """
        CREATE TABLE rps.tbl_rounds (
            fld_r_id_pk INTEGER PRIMARY KEY,
            fld_r_g_id_fk INTEGER NOT NULL,
            fld_r_p1_token CHAR(1) NOT NULL,
            fld_r_p2_token CHAR(1) NOT NULL,
            fld_r_doc TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fld_r_g_id_fk) REFERENCES rps.tbl_games(fld_g_id_pk),
            CHECK (fld_r_p1_token IN ('R', 'P', 'S')),
            CHECK (fld_r_p2_token IN ('R', 'P', 'S'))
        )
    """)

def create_errata_work(conn):
    """Create the errata table with composite primary key."""
    exec_sql(conn, """
        CREATE TABLE rps.tbl_errata (
            fld_e_doc TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            fld_e_message TEXT NOT NULL,
            PRIMARY KEY (fld_e_doc, fld_e_message)
        )
    """)

def verify_tables_work(conn):
    """Verify that all tables were created successfully."""
    query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'rps' 
        ORDER BY table_name
    """
    result = conn.execute(text(query)).fetchall()
    tables = [row[0] for row in result]
    
    expected_tables = ['tbl_errata', 'tbl_games', 'tbl_players', 'tbl_rounds']
    
    print("\nVerifying tables:")
    for table in expected_tables:
        if table in tables:
            print(f"  ✓ {table} exists")
        else:
            print(f"  ✗ {table} NOT found")
    
    return len(tables) == len(expected_tables)

try:
    # Start outer transaction
    with conn.begin():
        # Run all 5 blocks in order
        run_block(conn, "drop_tables", drop_tables_work)
        run_block(conn, "create_tbl_players", create_players_work)
        run_block(conn, "create_tbl_games", create_games_work)
        run_block(conn, "create_tbl_rounds", create_rounds_work)
        run_block(conn, "create_tbl_errata", create_errata_work)
    
    # If we reach here, all blocks succeeded
    print("success: all 5 blocks completed successfully")
    
    # Verify tables were created
    verify_tables_work(conn)

except BlockError as be:
    # A block failed; print error details and stop
    print(f"error occurred in: {be.block_name}")
    print(f"details: {be.original_exception}")
    # The outer transaction is automatically rolled back

finally:
    # Clean up connection
    conn.close()
