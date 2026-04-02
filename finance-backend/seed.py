from datetime import date
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.transaction import Transaction, TransactionType
from app.services.auth_service import hash_password

USERS = [
    {"username": "admin", "email": "admin@finance.dev", "password": "Admin@1234", "role": UserRole.admin},
    {"username": "analyst", "email": "analyst@finance.dev", "password": "Analyst@1234", "role": UserRole.analyst},
    {"username": "viewer", "email": "viewer@finance.dev", "password": "Viewer@1234", "role": UserRole.viewer},
]

TRANSACTIONS = [
    {"amount": 85000.0, "type": TransactionType.income, "category": "Salary", "date": date(2024, 1, 1), "notes": "January salary"},
    {"amount": 12000.0, "type": TransactionType.income, "category": "Freelance", "date": date(2024, 1, 15), "notes": "Web project"},
    {"amount": 3200.0, "type": TransactionType.expense, "category": "Rent", "date": date(2024, 1, 5)},
    {"amount": 1400.0, "type": TransactionType.expense, "category": "Utilities", "date": date(2024, 1, 10)},
    {"amount": 2800.0, "type": TransactionType.expense, "category": "Groceries", "date": date(2024, 1, 20)},
    {"amount": 85000.0, "type": TransactionType.income, "category": "Salary", "date": date(2024, 2, 1)},
    {"amount": 7500.0, "type": TransactionType.income, "category": "Freelance", "date": date(2024, 2, 18), "notes": "Logo design"},
    {"amount": 3200.0, "type": TransactionType.expense, "category": "Rent", "date": date(2024, 2, 5)},
    {"amount": 980.0, "type": TransactionType.expense, "category": "Subscriptions", "date": date(2024, 2, 12)},
    {"amount": 4500.0, "type": TransactionType.expense, "category": "Travel", "date": date(2024, 2, 25), "notes": "Client visit"},
    {"amount": 85000.0, "type": TransactionType.income, "category": "Salary", "date": date(2024, 3, 1)},
    {"amount": 3200.0, "type": TransactionType.expense, "category": "Rent", "date": date(2024, 3, 5)},
    {"amount": 6700.0, "type": TransactionType.expense, "category": "Equipment", "date": date(2024, 3, 14), "notes": "New monitor"},
    {"amount": 2100.0, "type": TransactionType.expense, "category": "Groceries", "date": date(2024, 3, 22)},
    {"amount": 15000.0, "type": TransactionType.income, "category": "Bonus", "date": date(2024, 3, 31), "notes": "Q1 performance bonus"},
]


def run():
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("Database already seeded. Skipping.")
            return

        created_users = []
        for u in USERS:
            user = User(
                username=u["username"],
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                role=u["role"],
            )
            db.add(user)
            created_users.append(user)

        db.flush()
        admin = next(u for u in created_users if u.role == UserRole.admin)

        for t in TRANSACTIONS:
            txn = Transaction(
                amount=t["amount"],
                type=t["type"],
                category=t["category"],
                date=t["date"],
                notes=t.get("notes"),
                created_by=admin.id,
            )
            db.add(txn)

        db.commit()
        print("Seed complete.")
        print("\nTest credentials:")
        for u in USERS:
            print(f"  {u['role'].value:10} → username: {u['username']:10} password: {u['password']}")

    finally:
        db.close()


if __name__ == "__main__":
    run()
