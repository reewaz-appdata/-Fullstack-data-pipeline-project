# assumptions:
# 1. sqlite is used for simplicity.
# 2. the database starts empty.
# 3. the script has permission to create and drop tables.
# 4. player_id, game_id, and round_id are auto-generated integers.
# 5. each game has exactly two players.
# 6. each round belongs to one game.


from sqlalchemy import create_engine, ForeignKey, String, Integer
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    sessionmaker,
    Session
)
from pydantic import BaseModel, StrictStr, StrictInt, ValidationError
from typing import List

# Create SQLite engine (file-based database)
engine = create_engine("sqlite:///rps.db", echo=False)

# Create session factory
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

class Player(Base):
    """Players table - stores each player."""
    __tablename__ = "players"

    player_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_name: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)

    # Relationships
    games_as_player1: Mapped[List["Game"]] = relationship(
        "Game",
        foreign_keys="Game.player1_id",
        back_populates="player1"
    )
    games_as_player2: Mapped[List["Game"]] = relationship(
        "Game",
        foreign_keys="Game.player2_id",
        back_populates="player2"
    )

    def __repr__(self):
        return f"Player(id={self.player_id}, name={self.player_name})"


class Game(Base):
    """Games table - stores games between two players."""
    __tablename__ = "games"

    game_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player1_id: Mapped[int] = mapped_column(ForeignKey("players.player_id"), nullable=False)
    player2_id: Mapped[int] = mapped_column(ForeignKey("players.player_id"), nullable=False)

    # Relationships
    player1: Mapped["Player"] = relationship(
        "Player",
        foreign_keys=[player1_id],
        back_populates="games_as_player1"
    )
    player2: Mapped["Player"] = relationship(
        "Player",
        foreign_keys=[player2_id],
        back_populates="games_as_player2"
    )
    rounds: Mapped[List["Round"]] = relationship(
        "Round",
        back_populates="game"
    )

    def __repr__(self):
        return f"Game(id={self.game_id}, player1_id={self.player1_id}, player2_id={self.player2_id})"


class Round(Base):
    """Rounds table - stores rounds within a game."""
    __tablename__ = "rounds"

    round_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.game_id"), nullable=False)
    player1_move: Mapped[str] = mapped_column(String(1), nullable=False)
    player2_move: Mapped[str] = mapped_column(String(1), nullable=False)

    # Relationships
    game: Mapped["Game"] = relationship(
        "Game",
        back_populates="rounds"
    )

    def __repr__(self):
        return f"Round(id={self.round_id}, game_id={self.game_id}, p1_move={self.player1_move}, p2_move={self.player2_move})"

class PlayerCreate(BaseModel):
    """Pydantic model for validating player input."""
    player_name: StrictStr


class GameCreate(BaseModel):
    """Pydantic model for validating game input."""
    player1_id: StrictInt
    player2_id: StrictInt


class RoundCreate(BaseModel):
    """Pydantic model for validating round input."""
    game_id: StrictInt
    player1_move: StrictStr
    player2_move: StrictStr

def reset_database():
    """Drop all tables and recreate them."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("[INFO] Database reset: all tables dropped and recreated.")


def create_player(session: Session, player_data: PlayerCreate) -> Player:
    """
    Insert a player into the database.
    
    Args:
        session: SQLAlchemy session
        player_data: Validated PlayerCreate object
    
    Returns:
        Inserted Player object with generated ID
    """
    player = Player(player_name=player_data.player_name)
    session.add(player)
    session.commit()
    session.refresh(player)
    return player


def create_game(session: Session, game_data: GameCreate) -> Game:
    """
    Insert a game into the database.
    
    Args:
        session: SQLAlchemy session
        game_data: Validated GameCreate object
    
    Returns:
        Inserted Game object with generated ID
    """
    game = Game(player1_id=game_data.player1_id, player2_id=game_data.player2_id)
    session.add(game)
    session.commit()
    session.refresh(game)
    return game


def create_round(session: Session, round_data: RoundCreate) -> Round:
    """
    Insert a round into the database.
    
    Args:
        session: SQLAlchemy session
        round_data: Validated RoundCreate object
    
    Returns:
        Inserted Round object with generated ID
    """
    round_obj = Round(
        game_id=round_data.game_id,
        player1_move=round_data.player1_move,
        player2_move=round_data.player2_move
    )
    session.add(round_obj)
    session.commit()
    session.refresh(round_obj)
    return round_obj


def main():
    """Main function demonstrating database operations with validation."""
    
    print("\n" + "="*70)
    print("ROCK-PAPER-SCISSORS DATABASE HOMEWORK")
    print("="*70 + "\n")
 
    reset_database()
  
    session = SessionLocal()

    print("\n" + "-"*70)
    print("SECTION 1: TESTING INVALID DATATYPES (Should Fail Validation)")
    print("-"*70 + "\n")
    
    # Invalid Player: player_name is integer instead of string
    print("[TEST 1] Invalid Player: player_name=123 (int instead of str)")
    try:
        bad_player = PlayerCreate(player_name=123)
        print("ERROR: Should have failed but didn't!\n")
    except ValidationError as e:
        print("✓ VALIDATION FAILED AS EXPECTED:")
        print(f"  {e.error_count()} error(s) detected\n")
    
    # Invalid Game: player1_id is string instead of int
    print("[TEST 2] Invalid Game: player1_id='one' (str instead of int)")
    try:
        bad_game = GameCreate(player1_id="one", player2_id=2)
        print("ERROR: Should have failed but didn't!\n")
    except ValidationError as e:
        print("✓ VALIDATION FAILED AS EXPECTED:")
        print(f"  {e.error_count()} error(s) detected\n")
    
    # Invalid Round: player1_move is integer instead of string
    print("[TEST 3] Invalid Round: player1_move=7 (int instead of str)")
    try:
        bad_round = RoundCreate(game_id=1, player1_move=7, player2_move="p")
        print("ERROR: Should have failed but didn't!\n")
    except ValidationError as e:
        print("✓ VALIDATION FAILED AS EXPECTED:")
        print(f"  {e.error_count()} error(s) detected\n")
    
    print("-"*70)
    print("SECTION 2: INSERTING VALID DATA (Should Succeed)")
    print("-"*70 + "\n")
    
    print("[INSERT 1] Creating player 'alice'...")
    player1_data = PlayerCreate(player_name="alice")
    player1 = create_player(session, player1_data)
    print(f"✓ Player inserted: {player1}\n")
    
    print("[INSERT 2] Creating player 'bob'...")
    player2_data = PlayerCreate(player_name="bob")
    player2 = create_player(session, player2_data)
    print(f"✓ Player inserted: {player2}\n")

    print("[INSERT 3] Creating game between alice (id={}) and bob (id={})...".format(
        player1.player_id, player2.player_id))
    game_data = GameCreate(player1_id=player1.player_id, player2_id=player2.player_id)
    game = create_game(session, game_data)
    print(f"✓ Game inserted: {game}\n")

    print("[INSERT 4] Creating round 1: alice plays 'r', bob plays 's'...")
    round1_data = RoundCreate(game_id=game.game_id, player1_move="r", player2_move="s")
    round1 = create_round(session, round1_data)
    print(f"✓ Round inserted: {round1}\n")
    
    print("[INSERT 5] Creating round 2: alice plays 'p', bob plays 'r'...")
    round2_data = RoundCreate(game_id=game.game_id, player1_move="p", player2_move="r")
    round2 = create_round(session, round2_data)
    print(f"✓ Round inserted: {round2}\n")
 
    print("-"*70)
    print("SECTION 3: DATABASE CONTENTS (Final Results)")
    print("-"*70 + "\n")
    
    # Query all players
    players = session.query(Player).all()
    print("[PLAYERS TABLE]")
    print(f"{'ID':<5} {'NAME':<20}")
    print("-" * 25)
    for player in players:
        print(f"{player.player_id:<5} {player.player_name:<20}")
    print()
    
    # Query all games
    games = session.query(Game).all()
    print("[GAMES TABLE]")
    print(f"{'ID':<5} {'PLAYER1_ID':<12} {'PLAYER2_ID':<12}")
    print("-" * 29)
    for game in games:
        print(f"{game.game_id:<5} {game.player1_id:<12} {game.player2_id:<12}")
    print()
    
    # Query all rounds
    rounds = session.query(Round).all()
    print("[ROUNDS TABLE]")
    print(f"{'ID':<5} {'GAME_ID':<10} {'P1_MOVE':<10} {'P2_MOVE':<10}")
    print("-" * 35)
    for round_obj in rounds:
        print(f"{round_obj.round_id:<5} {round_obj.game_id:<10} {round_obj.player1_move:<10} {round_obj.player2_move:<10}")
    print()
    
    session.close()
    print("\n" + "="*70)
    print("DATABASE SESSION CLOSED - HOMEWORK COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
