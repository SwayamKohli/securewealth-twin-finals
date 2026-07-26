"""
Seed Demo Data Script
====================
Populates the database with realistic sample data for demo user:
Email/Phone: +91-9876543210
MPIN: 123456
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID
import json

from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from models.user import User
from models.account import Account
from models.transaction import Transaction
from models.deposit import Deposit
from models.loan import Loan
from models.card import Card
from models.behavioural_profile import BehaviouralProfile
from models.enums import AccountType, TransactionChannel, TransactionStatus, LoanType, CardType, DepositType

def seed_demo_data():
    # Create database connection
    from core.config import settings
    engine = create_engine(settings.DATABASE_URL)
    
    with Session(engine) as db:
        # Find the demo user
        user = db.query(User).filter(User.phone == "9876543210").first()
        
        if not user:
            print("Demo user not found. Creating user...")
            user = User(
                user_id=UUID("9f7a90d8-9f4c-4802-8148-ed0756bf5ba8"),  # Use the user ID from logs
                full_name="Swayam Kohli",
                phone="9876543210",
                email="swayam@example.com",
                date_of_birth=datetime(1995, 5, 15),
                risk_profile="MODERATE",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created user: {user.full_name}")
        else:
            print(f"Found existing user: {user.full_name}")
        
        # Clear existing data for this user to start fresh
        from database.repositories.account_repository import AccountRepository
        from database.repositories.transaction_repository import TransactionRepository
        from database.repositories.deposit_repository import DepositRepository
        from database.repositories.loan_repository import LoanRepository
        from database.repositories.card_repository import CardRepository
        
        # Delete existing user data
        db.query(Account).filter(Account.user_id == user.user_id).delete()
        db.query(Transaction).filter(Transaction.user_id == user.user_id).delete()
        db.query(Deposit).filter(Deposit.user_id == user.user_id).delete()
        db.query(Loan).filter(Loan.user_id == user.user_id).delete()
        db.query(Card).filter(Card.user_id == user.user_id).delete()
        db.query(BehaviouralProfile).filter(BehaviouralProfile.user_id == user.user_id).delete()
        
        print("Cleared existing user data")
        
        # Create sample accounts
        print("Creating sample accounts...")
        account1 = Account(
            user_id=user.user_id,
            bank_name="Punjab & Sind Bank",
            account_type=AccountType.SAVINGS,
            account_number_masked="XXXXXXXX9012",
            balance=Decimal("125000.00"),
            currency="INR"
        )
        db.add(account1)
        db.commit()
        db.refresh(account1)
        
        account2 = Account(
            user_id=user.user_id,
            bank_name="HDFC Bank",
            account_type=AccountType.CURRENT,
            account_number_masked="XXXXXXXX5678",
            balance=Decimal("75000.00"),
            currency="INR"
        )
        db.add(account2)
        db.commit()
        db.refresh(account2)
        
        # Create sample deposits
        print("Creating sample deposits...")
        fd1 = Deposit(
            user_id=user.user_id,
            deposit_type=DepositType.FD,
            principal=Decimal("200000.00"),
            interest_rate=Decimal("7.5"),
            start_date=datetime(2025, 1, 15),
            maturity_date=datetime(2026, 1, 15),
            institution="State Bank of India"
        )
        db.add(fd1)
        
        rd1 = Deposit(
            user_id=user.user_id,
            deposit_type=DepositType.RD,
            principal=Decimal("50000.00"),
            interest_rate=Decimal("6.8"),
            start_date=datetime(2025, 6, 1),
            maturity_date=datetime(2027, 6, 1),
            institution="ICICI Bank"
        )
        db.add(rd1)
        db.commit()
        
        # Create sample loans
        print("Creating sample loans...")
        loan1 = Loan(
            user_id=user.user_id,
            loan_type=LoanType.PERSONAL,
            outstanding_amount=Decimal("150000.00"),
            emi=Decimal("12000.00"),
            interest_rate=Decimal("11.5"),
            remaining_tenure=12
        )
        db.add(loan1)
        
        loan2 = Loan(
            user_id=user.user_id,
            loan_type=LoanType.HOME,
            outstanding_amount=Decimal("2500000.00"),
            emi=Decimal("25000.00"),
            interest_rate=Decimal("8.5"),
            remaining_tenure=180
        )
        db.add(loan2)
        db.commit()
        
        # Create sample cards
        print("Creating sample cards...")
        card1 = Card(
            user_id=user.user_id,
            card_type=CardType.CREDIT,
            issuer="HDFC",
            reward_type="Cashback",
            cashback_rate=Decimal("1.5"),
            credit_limit=Decimal("150000.00")
        )
        db.add(card1)
        
        card2 = Card(
            user_id=user.user_id,
            card_type=CardType.DEBIT,
            issuer="Punjab & Sind Bank",
            reward_type="Rewards Points",
            cashback_rate=Decimal("0.5"),
            credit_limit=Decimal("0.00")  # Debit card has no credit limit
        )
        db.add(card2)
        db.commit()
        
        # Create sample transactions (last 30 days)
        print("Creating sample transactions...")
        from random import randint, choice
        
        merchants = [
            ("Amazon India", "E-commerce"),
            ("Reliance Fresh", "Grocery"),
            ("Starbucks", "Food & Beverage"),
            ("Uber", "Transport"),
            ("Swiggy", "Food Delivery"),
            ("Flipkart", "E-commerce"),
            ("IRCTC", "Travel"),
            ("Netflix", "Entertainment"),
            ("Spotify", "Entertainment"),
            ("Zomato", "Food Delivery")
        ]
        
        channels = [TransactionChannel.UPI, TransactionChannel.CARD]
        
        base_date = datetime.now() - timedelta(days=30)
        for i in range(45):  # Create 45 transactions over last 30 days
            days_back = randint(0, 29)
            transaction_time = base_date + timedelta(days=days_back, hours=randint(9, 21), minutes=randint(0, 59))
            
            merchant = choice(merchants)
            channel = choice(channels)
            
            # Vary transaction amounts realistically
            if i % 10 == 0:  # Every 10th transaction is larger (salary, bill payment, etc.)
                amount = Decimal(str(randint(10000, 50000)))
            else:
                amount = Decimal(str(randint(100, 5000)))
            
            transaction = Transaction(
                user_id=user.user_id,
                account_id=account1.account_id,
                amount=amount,
                merchant_name=merchant[0],
                merchant_category=merchant[1],
                channel=channel.value,
                transaction_time=transaction_time,
                status=TransactionStatus.SUCCESS,
                decision="ALLOW",  # Most transactions are allowed
                decision_timestamp=transaction_time
            )
            db.add(transaction)
        
        db.commit()
        
        # Create behavioral profile
        print("Creating behavioral profile...")
        
        profile = BehaviouralProfile(
            user_id=user.user_id,
            active_hours=json.dumps(list(range(9, 18))),  # 9 AM to 6 PM
            average_otp_time=Decimal("4.5"),
            round_number_frequency=Decimal("0.12"),
            transaction_velocity=Decimal("2.5"),
            baseline_metadata=json.dumps({
                "avg_monthly_income": 80000,
                "avg_monthly_expenses": 50000,
                "preferred_channels": ["UPI", "CARD"],
                "active_days": [0, 1, 2, 3, 4, 5, 6]  # All days
            }),
            last_updated=datetime.now()  # FIXED: Add the required last_updated field
        )
        db.add(profile)
        db.commit()
        
        print("✅ Demo data seeding completed successfully!")
        print(f"User: {user.full_name}")
        print(f"Accounts: 2")
        print(f"Deposits: 2")
        print(f"Loans: 2")
        print(f"Cards: 2")
        print(f"Transactions: 45")
        print(f"All data is ready for demonstration.")

if __name__ == "__main__":
    seed_demo_data()