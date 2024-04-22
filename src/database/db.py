from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

from src.conf.config import settings


engine = create_engine(settings.sqlalchemy_database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Provides a database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
