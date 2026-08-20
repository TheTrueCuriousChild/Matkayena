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
        import uuid
        from backend.services.shared.models import Product, Role, Customer, CustomerProduct, Profile

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified/initialized successfully in Supabase/PostgreSQL.")

        # Auto-seed baseline data if empty
        db = SessionLocal()
        try:
            prod_ins_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "prod_ins_1"))
            prod_mf_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "prod_mf_1"))
            prod_eq_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "prod_eq_1"))
            cust_101_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cust_101"))
            rm_priya_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "rm_priya_01"))

            if not db.query(Product).first():
                products = [
                    Product(id=prod_ins_id, code="TERM_LIFE", name="Term Life Insurance", category="INSURANCE", description="Comprehensive term protection policy"),
                    Product(id=prod_mf_id, code="BLUECHIP_MF", name="Bluechip Equity MF", category="MUTUAL_FUND", description="Diversified large cap mutual fund"),
                    Product(id=prod_eq_id, code="EQUITY_PMS", name="Equity PMS", category="EQUITY", description="High-alpha portfolio management service"),
                ]
                db.add_all(products)
                db.commit()
                logger.info("Auto-seeded baseline products (Insurance, Mutual Funds, PMS).")

            if not db.query(Profile).filter(Profile.id == rm_priya_id).first():
                sample_rm = Profile(
                    id=rm_priya_id,
                    employee_code="EMP_RM_01",
                    full_name="Priya Sharma",
                    email="priya@crm.com",
                    is_active=True
                )
                db.add(sample_rm)
                db.commit()
                logger.info("Auto-seeded sample RM Profile (Priya Sharma).")

            if not db.query(Customer).filter(Customer.customer_code == "CUST_101").first():
                sample_cust = Customer(
                    id=cust_101_id,
                    customer_code="CUST_101",
                    full_name="Vikram Malhotra",
                    email="vikram.malhotra@crm.com",
                    phone="+919876543210",
                    segment="ULTRA_HNI",
                    potential_value=2500000.0,
                    rm_id=rm_priya_id,
                    lifecycle_status="ACTIVE"
                )
                db.add(sample_cust)
                db.commit()

                # Add initial MF holding for cross-sell detection
                holding = CustomerProduct(
                    id=str(uuid.uuid4()),
                    customer_id=cust_101_id,
                    product_id=prod_mf_id,
                    status="ACTIVE",
                    relationship_value=2500000.0
                )
                db.add(holding)
                db.commit()
                logger.info("Auto-seeded sample customer CUST_101 with Mutual Fund holding.")

        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Database initialization note: {e}")


