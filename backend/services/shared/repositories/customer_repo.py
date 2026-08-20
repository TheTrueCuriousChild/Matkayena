"""Repository for Customer, Product, Holdings, Transactions, and Interactions."""

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.services.shared.models import (
    Customer, Product, CustomerProduct, Transaction, Interaction
)


class CustomerRepository:
    @staticmethod
    def get_by_id(db: Session, customer_id: str) -> Optional[Customer]:
        return db.query(Customer).filter(Customer.id == customer_id).first()

    @staticmethod
    def get_by_code(db: Session, customer_code: str) -> Optional[Customer]:
        return db.query(Customer).filter(Customer.customer_code == customer_code).first()

    @staticmethod
    def list_by_rm(db: Session, rm_id: str, skip: int = 0, limit: int = 100) -> List[Customer]:
        return db.query(Customer).filter(Customer.primary_rm_id == rm_id).offset(skip).limit(limit).all()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100) -> List[Customer]:
        return db.query(Customer).offset(skip).limit(limit).all()

    @staticmethod
    def create_customer(db: Session, customer: Customer) -> Customer:
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def get_holdings(db: Session, customer_id: str) -> List[CustomerProduct]:
        return db.query(CustomerProduct).filter(
            CustomerProduct.customer_id == customer_id,
            CustomerProduct.status == "ACTIVE"
        ).all()

    @staticmethod
    def get_transactions(db: Session, customer_id: str, limit: int = 50) -> List[Transaction]:
        return db.query(Transaction).filter(
            Transaction.customer_id == customer_id
        ).order_by(Transaction.occurred_at.desc()).limit(limit).all()

    @staticmethod
    def get_interactions(db: Session, customer_id: str, limit: int = 50) -> List[Interaction]:
        return db.query(Interaction).filter(
            Interaction.customer_id == customer_id
        ).order_by(Interaction.occurred_at.desc()).limit(limit).all()

    @staticmethod
    def create_transaction(db: Session, transaction: Transaction) -> Transaction:
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction

    @staticmethod
    def get_product_by_id(db: Session, product_id: str) -> Optional[Product]:
        return db.query(Product).filter(Product.id == product_id).first()

    @staticmethod
    def get_product_by_code(db: Session, code: str) -> Optional[Product]:
        return db.query(Product).filter(Product.code == code).first()

    @staticmethod
    def list_products(db: Session, active_only: bool = True) -> List[Product]:
        query = db.query(Product)
        if active_only:
            query = query.filter(Product.is_active.is_(True))
        return query.all()
