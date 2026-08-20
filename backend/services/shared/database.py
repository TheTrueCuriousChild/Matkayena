"""Database connection, session management, and Base for PS-02 CRM."""

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.services.shared.config import settings

logger = logging.getLogger("database")

# Base Declarative Model
Base = declarative_base()

def get_engine():
    db_url = settings.get_effective_db_url()
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    else:
        # PostgreSQL pool settings
        return create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=1800,
            pool_pre_ping=True,
        )
    return create_engine(db_url, connect_args=connect_args)

engine = get_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI Dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes schema tables and seeds baseline products & sample data if empty."""
    try:
        from backend.services.shared.models import Product, Role, Customer, CustomerProduct

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/initialized successfully in Supabase/PostgreSQL.")

        # Auto-seed baseline data if empty
        db = SessionLocal()
        try:
            if not db.query(Product).first():
                products = [
                    Product(id="prod_ins_1", code="TERM_LIFE", name="Term Life Insurance", category="INSURANCE", base_commission_rate=0.05),
                    Product(id="prod_mf_1", code="BLUECHIP_MF", name="Bluechip Equity MF", category="MUTUAL_FUND", base_commission_rate=0.015),
                    Product(id="prod_eq_1", code="EQUITY_PMS", name="Equity PMS", category="EQUITY", base_commission_rate=0.010),
                ]
                db.add_all(products)
                db.commit()
                logger.info("Auto-seeded baseline products (Insurance, Mutual Funds, PMS).")

            if not db.query(Customer).filter(Customer.id == "cust_101").first():
                sample_cust = Customer(
                    id="cust_101",
                    customer_code="CUST_101",
                    first_name="Vikram",
                    last_name="Malhotra",
                    segment="ULTRA_HNI",
                    relationship_value=2500000.0,
                    primary_rm_id="rm_priya_01",
                    status="ACTIVE"
                )
                db.add(sample_cust)
                db.commit()

                # Add initial MF holding for cross-sell detection
                holding = CustomerProduct(
                    customer_id="cust_101",
                    product_id="prod_mf_1",
                    holding_value=2500000.0
                )
                db.add(holding)
                db.commit()
                logger.info("Auto-seeded sample customer cust_101 with Mutual Fund holding.")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Database initialization note: {e}")

