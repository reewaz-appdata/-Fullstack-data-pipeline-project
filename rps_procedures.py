
"""Rock-Paper-Scissors Stored Procedures Implementation
Uses SQLAlchemy with raw SQL to implement PostgreSQL stored procedures
Error Code Mapping:
    proc_insert_player:
        0 = success
        1 = null or empty player name
        2 = duplicate player name
        -1 = unexpected exception

    proc_insert_game:
        0 = success
        1 = player1 is null or empty
        2 = player2 is null or empty
        3 = players are equal (after normalization)
        4 = player1 does not exist in tbl_players
        5 = player2 does not exist in tbl_players
        6 = duplicate game pair
        -1 = unexpected exception
"""

from sqlalchemy import create_engine, text
import sys

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

try:
    engine = create_engine(DATABASE_URL, echo=False)
except Exception as e:
    print(f"Error connecting to database: {e}")
    print("Make sure PostgreSQL is running and credentials are correct.")
    sys.exit(1)

schema_sql = """
DROP SCHEMA IF EXISTS rps CASCADE;
CREATE SCHEMA rps;
"""

table_creation_sql = """
-- Create players table
CREATE TABLE rps.tbl_players (
    fld_player_id SERIAL PRIMARY KEY,
    fld_player_name CHAR(16) NOT NULL UNIQUE,
    fld_created_at TIMESTAMP DEFAULT NOW()
);

-- Create sequence for games
CREATE SEQUENCE rps.rps_seq START 1 INCREMENT 1;

-- Create games table
CREATE TABLE rps.tbl_games (
    fld_g_id_pk BIGINT PRIMARY KEY DEFAULT NEXTVAL('rps.rps_seq'),
    fld_player1 CHAR(16) NOT NULL,
    fld_player2 CHAR(16) NOT NULL,
    fld_created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (fld_player1) REFERENCES rps.tbl_players(fld_player_name),
    FOREIGN KEY (fld_player2) REFERENCES rps.tbl_players(fld_player_name)
);

-- Create error/exception log table
CREATE TABLE rps.tbl_errata (
    fld_errata_id SERIAL PRIMARY KEY,
    fld_sqlstate CHAR(5),
    fld_sqlerrm TEXT,
    fld_logged_at TIMESTAMP DEFAULT NOW()
);
"""

proc_insert_player_sql = """
CREATE OR REPLACE PROCEDURE rps.proc_insert_player(
    IN p_player_name CHAR(16),
    INOUT p_errlvl SMALLINT
)
LANGUAGE plpgsql
AS $proc_insert_player$
BEGIN
    -- Initialize error level to success
    p_errlvl := 0;
    
    -- Check if player name is null or empty (trim whitespace)
    IF p_player_name IS NULL OR TRIM(p_player_name) = '' THEN
        p_errlvl := 1;
    -- Check if player already exists
    ELSEIF EXISTS(
        SELECT *
        FROM rps.tbl_players
        WHERE fld_player_name = p_player_name
    ) THEN
        p_errlvl := 2;
    -- Insert player if all validations pass
    ELSE
        INSERT INTO rps.tbl_players(fld_player_name)
        VALUES(p_player_name);
        p_errlvl := 0;
    END IF;
    
EXCEPTION
    WHEN OTHERS THEN
        INSERT INTO rps.tbl_errata(fld_sqlstate, fld_sqlerrm)
        VALUES(SQLSTATE, SQLERRM);
        RAISE WARNING 'Unexpected error in proc_insert_player: %', SQLERRM;
        p_errlvl := -1;
END $proc_insert_player$;
"""
proc_insert_game_sql = """
CREATE OR REPLACE PROCEDURE rps.proc_insert_game(
    IN p_player1 CHAR(16),
    IN p_player2 CHAR(16),
    INOUT p_errlvl SMALLINT
)
LANGUAGE plpgsql
AS $proc_insert_game$
DECLARE
    v_player1 CHAR(16);
    v_player2 CHAR(16);
BEGIN
    -- Initialize error level to success
    p_errlvl := 0;
    
    -- Check if player1 is null or empty
    IF p_player1 IS NULL OR TRIM(p_player1) = '' THEN
        p_errlvl := 1;
    -- Check if player2 is null or empty
    ELSEIF p_player2 IS NULL OR TRIM(p_player2) = '' THEN
        p_errlvl := 2;
    -- Proceed with normalization and validation
    ELSE
        -- Normalize player order (ensure player1 < player2)
        IF p_player1 < p_player2 THEN
            v_player1 := p_player1;
            v_player2 := p_player2;
        ELSE
            v_player1 := p_player2;
            v_player2 := p_player1;
        END IF;
        
        -- Check if players are equal
        IF v_player1 = v_player2 THEN
            p_errlvl := 3;
        -- Check if player1 exists
        ELSEIF NOT EXISTS(
            SELECT *
            FROM rps.tbl_players
            WHERE fld_player_name = v_player1
        ) THEN
            p_errlvl := 4;
        -- Check if player2 exists
        ELSEIF NOT EXISTS(
            SELECT *
            FROM rps.tbl_players
            WHERE fld_player_name = v_player2
        ) THEN
            p_errlvl := 5;
        -- Check for duplicate game pair
        ELSEIF EXISTS(
            SELECT *
            FROM rps.tbl_games
            WHERE fld_player1 = v_player1 AND fld_player2 = v_player2
        ) THEN
            p_errlvl := 6;
        -- Insert game if all validations pass
        ELSE
            INSERT INTO rps.tbl_games(fld_player1, fld_player2)
            VALUES(v_player1, v_player2);
            p_errlvl := 0;
        END IF;
    END IF;
    
EXCEPTION
    WHEN OTHERS THEN
        INSERT INTO rps.tbl_errata(fld_sqlstate, fld_sqlerrm)
        VALUES(SQLSTATE, SQLERRM);
        RAISE WARNING 'Unexpected error in proc_insert_game: %', SQLERRM;
        p_errlvl := -1;
END $proc_insert_game$;
"""

def setup_database():
    """Create schema, tables, and stored procedures"""
    print("=" * 70)
    print("SETTING UP DATABASE")
    print("=" * 70)
    
    # Create schema
    print("\n1. Creating schema rps...")
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text(schema_sql))
    print("   Schema created successfully.")
    
    # Create tables
    print("2. Creating tables and sequence...")
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text(table_creation_sql))
    print("   Tables and sequence created successfully.")
    
    # Create first stored procedure (separate context)
    print("3. Creating proc_insert_player (separate execution context)...")
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text(proc_insert_player_sql))
    print("   proc_insert_player created successfully.")
    
    # Create second stored procedure (separate context)
    print("4. Creating proc_insert_game (separate execution context)...")
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text(proc_insert_game_sql))
    print("   proc_insert_game created successfully.")

def verify_procedures_stored():
    """Query information_schema to verify procedures exist in database"""
    print("\n" + "=" * 70)
    print("VERIFICATION: PROCEDURES STORED IN DATABASE")
    print("=" * 70)
    
    query = """
    SELECT routine_schema, routine_name, routine_type
    FROM information_schema.routines
    WHERE routine_schema = 'rps'
    AND routine_type = 'PROCEDURE'
    ORDER BY routine_name;
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(query))
        procedures = result.fetchall()
    
    if procedures:
        print("\nStored procedures found in schema 'rps':")
        print("-" * 70)
        for row in procedures:
            schema, name, routine_type = row
            print(f"  Schema: {schema:15} Name: {name:30} Type: {routine_type}")
    else:
        print("WARNING: No procedures found in rps schema!")
    
    return procedures

def execute_insert_player_test(player_name):
    """
    Execute proc_insert_player test by calling the procedure in an anonymous block
    Returns the error level. Handles NULL properly.
    
    FIX: All operations in a single connection to ensure temp table is available.
    FIX: Proper NULL handling - if player_name is None, use NULL::CHAR(16).
    """
    # Build the player parameter safely
    if player_name is None:
        player_param = "NULL::CHAR(16)"
    else:
        # Escape single quotes in player name (defensive)
        safe_name = player_name.replace("'", "''")
        player_param = f"'{safe_name}'::CHAR(16)"
    
    # All operations in a single connection/transaction
    with engine.connect() as conn:
        with conn.begin():
            # Create temp table
            conn.execute(text("""
                DROP TABLE IF EXISTS _procedure_result;
                CREATE TEMP TABLE _procedure_result (result_value SMALLINT);
            """))
            
            # Execute the procedure call in a block
            block_sql = f"""
            DO $execute$
            DECLARE
                v_err SMALLINT := 0;
            BEGIN
                CALL rps.proc_insert_player({player_param}, v_err);
                INSERT INTO _procedure_result(result_value) VALUES(v_err);
            END $execute$;
            """
            conn.execute(text(block_sql))
            
            # Read the result immediately in same connection
            result = conn.execute(text("SELECT result_value FROM _procedure_result;"))
            row = result.fetchone()
            errlvl = row[0] if row else -999
    
    return errlvl

def execute_insert_game_test(player1, player2):
    """
    Execute proc_insert_game test by calling the procedure in an anonymous block.
    Returns the error level. Handles NULL and empty strings properly.
    
    FIX: All operations in a single connection to ensure temp table is available.
    FIX: Proper NULL handling for both parameters.
    """
    # Build the player1 parameter safely
    if player1 is None:
        p1_param = "NULL::CHAR(16)"
    else:
        # Escape single quotes (defensive)
        safe_p1 = player1.replace("'", "''")
        p1_param = f"'{safe_p1}'::CHAR(16)" if player1 else "''"
    
    # Build the player2 parameter safely
    if player2 is None:
        p2_param = "NULL::CHAR(16)"
    else:
        # Escape single quotes (defensive)
        safe_p2 = player2.replace("'", "''")
        p2_param = f"'{safe_p2}'::CHAR(16)" if player2 else "''"
    
    # All operations in a single connection/transaction
    with engine.connect() as conn:
        with conn.begin():
            # Create temp table
            conn.execute(text("""
                DROP TABLE IF EXISTS _procedure_result;
                CREATE TEMP TABLE _procedure_result (result_value SMALLINT);
            """))
            
            # Execute the procedure call in a block
            block_sql = f"""
            DO $execute$
            DECLARE
                v_err SMALLINT := 0;
            BEGIN
                CALL rps.proc_insert_game({p1_param}, {p2_param}, v_err);
                INSERT INTO _procedure_result(result_value) VALUES(v_err);
            END $execute$;
            """
            conn.execute(text(block_sql))
            
            # Read the result immediately in same connection
            result = conn.execute(text("SELECT result_value FROM _procedure_result;"))
            row = result.fetchone()
            errlvl = row[0] if row else -999
    
    return errlvl

def test_proc_insert_player():
    """Test proc_insert_player with valid and invalid inputs"""
    print("\n" + "=" * 70)
    print("TEST SUITE: proc_insert_player(p_player_name, p_errlvl)")
    print("=" * 70)
    
    print("\nVALID TESTS:")
    print("-" * 70)
    
    # Valid test 1: Insert 'Al'
    print("Test 1: proc_insert_player('Al')")
    errlvl = execute_insert_player_test('Al')
    print(f"  Result: errlvl = {errlvl}")
    print(f"  Expected: 0 (success)")
    print(f"  Status: {'PASS' if errlvl == 0 else 'FAIL'}\n")
    
    # Valid test 2: Insert 'Bob'
    print("Test 2: proc_insert_player('Bob')")
    errlvl = execute_insert_player_test('Bob')
    print(f"  Result: errlvl = {errlvl}")
    print(f"  Expected: 0 (success)")
    print(f"  Status: {'PASS' if errlvl == 0 else 'FAIL'}\n")
    
    # Valid test 3: Insert 'Chas'
    print("Test 3: proc_insert_player('Chas')")
    errlvl = execute_insert_player_test('Chas')
    print(f"  Result: errlvl = {errlvl}")
    print(f"  Expected: 0 (success)")
    print(f"  Status: {'PASS' if errlvl == 0 else 'FAIL'}\n")
    
    print("INVALID TESTS:")
    print("-" * 70)
    
    # Invalid test 1: NULL player name
    print("Test 4: proc_insert_player(NULL)")
    errlvl = execute_insert_player_test(None)
    print(f"  Result: errlvl = {errlvl}")
    print(f"  Expected: 1 (null or empty)")
    print(f"  Status: {'PASS' if errlvl == 1 else 'FAIL'}\n")
    
    # Invalid test 2: Empty player name
    print("Test 5: proc_insert_player('')")
    errlvl = execute_insert_player_test('')
    print(f"  Result: errlvl = {errlvl}")
    print(f"  Expected: 1 (null or empty)")
    print(f"  Status: {'PASS' if errlvl == 1 else 'FAIL'}\n")
    
    # Invalid test 3: Duplicate player name
    print("Test 6: proc_insert_player('Al') [duplicate]")
    errlvl = execute_insert_player_test('Al')
    print(f"  Result: errlvl = {errlvl}")
    print(f"  Expected: 2 (duplicate player)")
    print(f"  Status: {'PASS' if errlvl == 2 else 'FAIL'}\n")

def test_proc_insert_game():
    """Test proc_insert_game with valid and invalid inputs"""
    print("\n" + "=" * 70)
    print("TEST SUITE: proc_insert_game(p_player1, p_player2, p_errlvl)")
    print("=" * 70)
    
    print("\nVALID TESTS:")
    print("-" * 70)
    
    # Valid test 1: Insert game ('Al', 'Bob')
    print("Test 1: proc_insert_game('Al', 'Bob')")
    errlvl = execute_insert_game_test('Al', 'Bob')
    print(f"  Result: errlvl = {errlvl}")
    print(f"  Expected: 0 (success)")
    print(f"  Status: {'PASS' if errlvl == 0 else 'FAIL'}\n")
    
    # Valid test 2: Insert game ('Chas', 'Bob') - should be swapped to ('Bob', 'Chas')
    print("Test 2: proc_insert_game('Chas', 'Bob') [reversed, should normalize]")
    errlvl = execute_insert_game_test('Chas', 'Bob')
    print(f"  Result: errlvl = {errlvl}")
    print(f"  Expected: 0 (success, normalized to Bob/Chas)")
    print(f"  Status: {'PASS' if errlvl == 0 else 'FAIL'}\n")
    
    print("INVALID TESTS:")
    print("-" * 70)
    
    # Invalid test 1: player1 is NULL
    print("Test 3: proc_insert_game(NULL, 'Bob')")
    errlvl = execute_insert_game_test(None, 'Bob')
    print(f"  Result: errlvl = {errlvl}")
    print(f"  Expected: 1 (player1 is null/empty)")
    print(f"  Status: {'PASS' if errlvl == 1 else 'FAIL'}\n")
    
    # Invalid test 2: player2 is empty
    print("Test 4: proc_insert_game('Bob', '')")
    errlvl = execute_insert_game_test('Bob', '')
    print(f"  Result: errlvl = {errlvl}")
    print(f"  Expected: 2 (player2 is null/empty)")
    print(f"  Status: {'PASS' if errlvl == 2 else 'FAIL'}\n")
    
    # Invalid test 3: player1 does not exist
    print("Test 5: proc_insert_game('Al', 'Bogus')")
    errlvl = execute_insert_game_test('Al', 'Bogus')
    print(f"  Result: errlvl = {errlvl}")
    print(f"  Expected: 5 (player2 not found after normalization)")
    print(f"  Status: {'PASS' if errlvl == 5 else 'FAIL'}\n")
    
    # Invalid test 4: Duplicate game pair
    print("Test 6: proc_insert_game('Al', 'Bob') [duplicate]")
    errlvl = execute_insert_game_test('Al', 'Bob')
    print(f"  Result: errlvl = {errlvl}")
    print(f"  Expected: 6 (duplicate game pair)")
    print(f"  Status: {'PASS' if errlvl == 6 else 'FAIL'}\n")
    
    # Invalid test 5: Reverse duplicate (should also be caught)
    print("Test 7: proc_insert_game('Bob', 'Al') [reverse of existing pair]")
    errlvl = execute_insert_game_test('Bob', 'Al')
    print(f"  Result: errlvl = {errlvl}")
    print(f"  Expected: 6 (duplicate game pair, normalized to existing Al/Bob)")
    print(f"  Status: {'PASS' if errlvl == 6 else 'FAIL'}\n")
    
    # Invalid test 6: Players are equal
    print("Test 8: proc_insert_game('Al', 'Al') [equal players]")
    errlvl = execute_insert_game_test('Al', 'Al')
    print(f"  Result: errlvl = {errlvl}")
    print(f"  Expected: 3 (players are equal)")
    print(f"  Status: {'PASS' if errlvl == 3 else 'FAIL'}\n")

def display_table_contents():
    """Display contents of all tables after testing"""
    print("\n" + "=" * 70)
    print("FINAL TABLE CONTENTS")
    print("=" * 70)
    
    # Display tbl_players
    print("\nrps.tbl_players:")
    print("-" * 70)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT fld_player_id, fld_player_name, fld_created_at
            FROM rps.tbl_players
            ORDER BY fld_player_id;
        """))
        rows = result.fetchall()
    
    if rows:
        print(f"{'ID':<5} {'Player Name':<20} {'Created At':<30}")
        print("-" * 70)
        for row in rows:
            player_id, player_name, created_at = row
            # Trim player name from CHAR(16)
            player_name = player_name.strip() if player_name else ""
            print(f"{player_id:<5} {player_name:<20} {str(created_at):<30}")
    else:
        print("  (no rows)")
    
    # Display tbl_games
    print("\nrps.tbl_games:")
    print("-" * 70)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT fld_g_id_pk, fld_player1, fld_player2, fld_created_at
            FROM rps.tbl_games
            ORDER BY fld_g_id_pk;
        """))
        rows = result.fetchall()
    
    if rows:
        print(f"{'Game ID':<12} {'Player 1':<20} {'Player 2':<20} {'Created At':<30}")
        print("-" * 70)
        for row in rows:
            game_id, player1, player2, created_at = row
            # Trim player names from CHAR(16)
            player1 = player1.strip() if player1 else ""
            player2 = player2.strip() if player2 else ""
            print(f"{game_id:<12} {player1:<20} {player2:<20} {str(created_at):<30}")
    else:
        print("  (no rows)")
    
    # Display tbl_errata
    print("\nrps.tbl_errata:")
    print("-" * 70)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT fld_errata_id, fld_sqlstate, fld_sqlerrm, fld_logged_at
            FROM rps.tbl_errata
            ORDER BY fld_errata_id;
        """))
        rows = result.fetchall()
    
    if rows:
        print(f"{'ID':<5} {'SQLSTATE':<12} {'Error Message':<50} {'Logged At':<30}")
        print("-" * 70)
        for row in rows:
            errata_id, sqlstate, sqlerrm, logged_at = row
            print(f"{errata_id:<5} {sqlstate:<12} {sqlerrm:<50} {str(logged_at):<30}")
    else:
        print("  (no rows)")


def main():
    """Main execution function"""
    try:
        # 1. Setup database
        setup_database()
        
        # 2. Verify procedures are stored
        verify_procedures_stored()
        
        # 3. Run test suites
        test_proc_insert_player()
        test_proc_insert_game()
        
        # 4. Display final results
        display_table_contents()
        
        print("\n" + "=" * 70)
        print("EXECUTION COMPLETE")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        engine.dispose()

if __name__ == "__main__":
    main()
