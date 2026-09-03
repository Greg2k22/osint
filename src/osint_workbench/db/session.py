from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from osint_workbench.settings import Settings


def create_session_factory(settings: Settings | None = None):
    cfg = settings or Settings()
    engine = create_engine(cfg.database_url, pool_pre_ping=True)
    return sessionmaker(bind=engine, expire_on_commit=False)
