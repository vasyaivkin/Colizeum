import datetime
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.orm import relationship

from bot.models.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    role = Column(String(20), nullable=False, default="owner")  # owner / manager
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())


class Invite(Base):
    __tablename__ = "invites"

    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    created_by = Column(BigInteger, nullable=False)
    used_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=func.now())
    used_at = Column(DateTime, nullable=True)


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=func.now())
    category = Column(String(50), nullable=False)  # bar/salary/fixed/other/utility
    amount = Column(Float, nullable=False)
    payment_type = Column(String(20), nullable=False)  # cash / card
    from_cash = Column(Boolean, default=False)
    comment = Column(Text, nullable=True)
    receipt_url = Column(Text, nullable=True)
    receipt_drive_id = Column(String(200), nullable=True)
    created_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=func.now())


class Income(Base):
    __tablename__ = "incomes"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=func.now())
    amount = Column(Float, nullable=False)
    payment_type = Column(String(20), nullable=False)  # cash / card
    source = Column(Text, nullable=True)
    destination = Column(String(50), nullable=True)  # cash / account / expenses
    comment = Column(Text, nullable=True)
    created_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=func.now())


class CashOperation(Base):
    __tablename__ = "cash_operations"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=func.now())
    operation_type = Column(String(30), nullable=False)  # terminal_cash / expense / income / opening
    amount = Column(Float, nullable=False)
    comment = Column(Text, nullable=True)
    balance_after = Column(Float, nullable=False, default=0)
    reference_id = Column(Integer, nullable=True)
    reference_type = Column(String(30), nullable=True)  # expense / income / shift
    created_at = Column(DateTime, default=func.now())


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    status = Column(String(30), nullable=False, default="active")
    # statuses: active / broken / repair / decommissioned
    pc_number = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)

    purchase_date = Column(DateTime, nullable=True)
    store = Column(String(200), nullable=True)
    price = Column(Float, nullable=True)
    warranty_months = Column(Integer, nullable=True)
    warranty_until = Column(DateTime, nullable=True)
    serial_number = Column(String(200), nullable=True)
    receipt_url = Column(Text, nullable=True)

    repair_master = Column(String(200), nullable=True)
    repair_date = Column(DateTime, nullable=True)
    repair_until = Column(DateTime, nullable=True)
    repair_cost = Column(Float, nullable=True)
    repair_warranty_months = Column(Integer, nullable=True)

    broken_date = Column(DateTime, nullable=True)
    broken_description = Column(Text, nullable=True)
    broken_by = Column(String(100), nullable=True)

    decommission_date = Column(DateTime, nullable=True)
    decommission_reason = Column(Text, nullable=True)

    created_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class InventoryCheck(Base):
    __tablename__ = "inventory_checks"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=func.now())
    conducted_by = Column(String(100), nullable=False)
    items_checked = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    result = Column(Text, nullable=True)
    created_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=func.now())


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="normal")
    # urgent / normal / low
    deadline = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    # pending / completed
    creator_id = Column(BigInteger, nullable=False)
    assignee_id = Column(BigInteger, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    completion_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    comments = relationship("TaskComment", back_populates="task", order_by="TaskComment.created_at")


class TaskComment(Base):
    __tablename__ = "task_comments"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())

    task = relationship("Task", back_populates="comments")


class Salary(Base):
    __tablename__ = "salaries"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    shift = Column(String(20), nullable=True)  # day / night
    employee_name = Column(String(100), nullable=False)
    employee_type = Column(String(20), nullable=False, default="admin")
    # admin / cleaner
    base_rate = Column(Float, nullable=False, default=0)
    points = Column(Integer, nullable=True, default=0)
    point_value = Column(Float, nullable=True, default=0)
    langame_cash = Column(Float, nullable=True, default=0)
    total = Column(Float, nullable=False, default=0)
    days_count = Column(Integer, nullable=True)  # for cleaners
    comment = Column(Text, nullable=True)
    created_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=func.now())


class Utility(Base):
    __tablename__ = "utilities"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=func.now())
    t1_reading = Column(Float, nullable=False)
    t2_reading = Column(Float, nullable=False)
    t1_prev = Column(Float, nullable=True)
    t2_prev = Column(Float, nullable=True)
    t1_kwh = Column(Float, nullable=True)
    t2_kwh = Column(Float, nullable=True)
    t1_rate = Column(Float, nullable=False)
    t2_rate = Column(Float, nullable=False)
    t1_amount = Column(Float, nullable=True)
    t2_amount = Column(Float, nullable=True)
    total = Column(Float, nullable=False, default=0)
    manual_total = Column(Float, nullable=True)  # if user overrides calculated total
    receipt_url = Column(Text, nullable=True)
    created_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=func.now())


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
