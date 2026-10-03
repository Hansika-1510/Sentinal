from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models so Base.metadata is populated
import app.models  # noqa
