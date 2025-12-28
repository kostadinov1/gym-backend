from sqlmodel import SQLModel, create_engine, Session

# For now, we use SQLite for the backend dev to move fast.
# In production (Render), we will swap this string for the Postgres URL.
DATABASE_URL = "sqlite:///./backend_gym.db"

# connect_args is needed only for SQLite
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)