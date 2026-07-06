from sqlalchemy import Table, Column, Integer, ForeignKey
from ..database import Base

expense_tag_map = Table(
    "expense_tag_map",
    Base.metadata,
    Column("expense_id", Integer, ForeignKey("expenses.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("expense_tags.id", ondelete="CASCADE"), primary_key=True),
)
