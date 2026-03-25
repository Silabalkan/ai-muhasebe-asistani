# db.py
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"   # proje klasöründe app.db

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite için gerekli
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_schema_compatibility():
    """Apply tiny, backward-compatible schema fixes for existing databases."""
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    if "users" in table_names:
        user_columns = {col["name"] for col in inspector.get_columns("users")}
        if "role" not in user_columns:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE users "
                        "ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'personel'"
                    )
                )


# Her request’te kullanılacak DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
