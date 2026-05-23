#Reewaz Rijal
# create_tables.py

import os

from sqlalchemy import (
    create_engine,
    text,
    Column,
    Integer,
    CHAR,
    Text,
    TIMESTAMP,
    CheckConstraint,
    UniqueConstraint,
    PrimaryKeyConstraint,
    ForeignKeyConstraint,
    func,
)
from sqlalchemy.orm import declarative_base
base = declarative_base()

SCHEMA_NAME = "rps"

class TblPlayers(base):
    __tablename__ = "tbl_players"
    __table_args__ = (
        PrimaryKeyConstraint("fld_p_id_pk", name="players_pk"),
        {"schema": SCHEMA_NAME},
    )

    fld_p_id_pk = Column(CHAR(16), nullable=False)
    fld_p_doc = Column(TIMESTAMP, server_default=func.now())

class TblGames(base):
    __tablename__ = "tbl_games"
    __table_args__ = (
        PrimaryKeyConstraint("fld_g_id_pk", name="games_pk"),
        ForeignKeyConstraint(
            ["fld_g_p1_id_fk"],
            [f"{SCHEMA_NAME}.tbl_players.fld_p_id_pk"],
            name="games_p1_fk",
        ),
        ForeignKeyConstraint(
            ["fld_g_p2_id_fk"],
            [f"{SCHEMA_NAME}.tbl_players.fld_p_id_pk"],
            name="games_p2_fk",
        ),
        UniqueConstraint("fld_g_p1_id_fk", "fld_g_p2_id_fk", name="games_players_unique"),
        CheckConstraint("fld_g_p1_id_fk < fld_g_p2_id_fk", name="games_players_order_chk"),
        {"schema": SCHEMA_NAME},
    )

    fld_g_id_pk = Column(Integer, nullable=False)
    fld_g_p1_id_fk = Column(CHAR(16), nullable=False)
    fld_g_p2_id_fk = Column(CHAR(16), nullable=False)
    fld_g_doc = Column(TIMESTAMP, server_default=func.now())

class TblRounds(base):
    __tablename__ = "tbl_rounds"
    __table_args__ = (
        PrimaryKeyConstraint("fld_r_id_pk", name="rounds_pk"),
        ForeignKeyConstraint(
            ["fld_r_g_id_fk"],
            [f"{SCHEMA_NAME}.tbl_games.fld_g_id_pk"],
            name="rounds_game_fk",
        ),
        CheckConstraint(
            "fld_r_p1_token IN ('R','P','S')",
            name="rounds_p1_token_chk",
        ),
        CheckConstraint(
            "fld_r_p2_token IN ('R','P','S')",
            name="rounds_p2_token_chk",
        ),
        {"schema": SCHEMA_NAME},
    )

    fld_r_id_pk = Column(Integer, nullable=False)
    fld_r_g_id_fk = Column(Integer, nullable=False)
    fld_r_p1_token = Column(CHAR(1), nullable=False)
    fld_r_p2_token = Column(CHAR(1), nullable=False)
    fld_r_doc = Column(TIMESTAMP, server_default=func.now())

class TblErrata(base):
    __tablename__ = "tbl_errata"
    __table_args__ = (
        PrimaryKeyConstraint("fld_e_doc", "fld_e_message", name="errata_pk"),
        {"schema": SCHEMA_NAME},
    )

    fld_e_doc = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    fld_e_message = Column(Text, nullable=False)

def main() -> None:
   
    engine = create_engine(
        "postgresql+psycopg2://postgres@/db55",
        echo=False,
        future=True
    )
    # create all tables
    base.metadata.create_all(engine)


if __name__ == "__main__":
    main()
