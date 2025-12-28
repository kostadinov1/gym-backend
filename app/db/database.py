from sqlmodel import SQLModel, create_engine, Session

# OLD (SQLite) - Comment this out
# DATABASE_URL = "sqlite:///./backend_gym.db"
# connect_args = {"check_same_thread": False}

# NEW (PostgreSQL)
# Note: 'localhost' works because you run Python natively and DB in Docker.
DATABASE_URL = "postgresql://gym_user:gym_password@localhost:5432/gym_db"
connect_args = {} # Postgres doesn't need the thread check

engine = create_engine(DATABASE_URL, connect_args=connect_args)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)