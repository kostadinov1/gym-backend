from sqlmodel import Session, select, SQLModel
from app.db.database import engine, create_db_and_tables
from app.db.models import Exercise, WorkoutPlan, WorkoutRoutine, RoutineExercise
from datetime import datetime, timedelta, timezone # <--- Add timezone

from app.db.models import User # Import User
from app.core.security import get_password_hash # Import hasher

def seed():
    SQLModel.metadata.drop_all(engine)
    create_db_and_tables()

    with Session(engine) as session:
        print("🌱 Seeding Database...")

        # 1. Create a Default User (So you can login immediately)
        default_user = User(
            email="test@gym.com",
            hashed_password=get_password_hash("123"),
            full_name="Test User"
        )
        session.add(default_user)
        session.commit() # Commit to get ID
        
        print(f"   Created User: {default_user.email} (Password: 123)")

        # 2. Create Exercises
        # System exercises have user_id=None (Global)
        deadlift = Exercise(name="Deadlift", default_increment=5.0, unit="kg", is_custom=False, user_id=None)
        pullups = Exercise(name="Pull Ups", default_increment=1.25, unit="kg", is_custom=False, user_id=None)
        rows = Exercise(name="Barbell Row", default_increment=2.5, unit="kg", is_custom=False, user_id=None)
        
        session.add(deadlift)
        session.add(pullups)
        session.add(rows)
        session.commit()

        # 3. Create a Plan (Owned by Default User)
        start = datetime.now(timezone.utc) 
        duration = 8
        end = start + timedelta(weeks=duration)

        plan = WorkoutPlan(
            name="Powerbuilder V1", 
            duration_weeks=duration, 
            start_date=start,
            end_date=end,
            user_id=default_user.id # <--- ASSIGN TO USER
        )
        session.add(plan)
        session.commit()

        # 4. Create a Routine (Pull Day A - Monday)
        routine_a = WorkoutRoutine(
            name="Pull Day A", 
            plan_id=plan.id, 
            day_of_week=0 # Monday
        )
        session.add(routine_a)
        session.commit()

        # 5. Link Exercises to Routine (The Targets)
        # Deadlift: 3 sets x 5 reps @ 100kg start, +5kg increment
        ex_1 = RoutineExercise(
            routine_id=routine_a.id,
            exercise_id=deadlift.id,
            order_index=1,
            target_sets=3,
            target_reps=5,
            target_weight=100.0,
            rest_seconds=180,
            increment_value=5.0
        )
        
        # Pullups: 3 sets x 8 reps @ 0kg (Bodyweight), +1.25kg increment
        ex_2 = RoutineExercise(
            routine_id=routine_a.id,
            exercise_id=pullups.id,
            order_index=2,
            target_sets=3,
            target_reps=8,
            target_weight=0.0,
            rest_seconds=120,
            increment_value=1.25
        )

        session.add(ex_1)
        session.add(ex_2)
        session.commit()
        
        print("✅ Database Seeded successfully!")
        print(f"   Created Plan: {plan.name}")
        print(f"   Created Routine: {routine_a.name} with Deadlifts & Pullups")

if __name__ == "__main__":
    seed()