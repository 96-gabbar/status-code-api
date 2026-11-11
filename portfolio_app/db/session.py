from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from portfolio_app.config import PortfolioSettings


def create_portfolio_db_engine(settings: PortfolioSettings) -> Engine:
    return create_engine(
        settings.database_url.get_secret_value(),
        echo=settings.sql_echo,
        pool_pre_ping=True,
    )


def create_portfolio_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )
