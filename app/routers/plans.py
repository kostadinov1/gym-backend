from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, col, or_
from typing import List
from datetime import timedelta, datetime
import uuid

from app.db.database import get_session
from app.db.models import WorkoutPlan, WorkoutRoutine, RoutineExercise, WorkoutSession
from app.schemas.plan import PlanCreate, PlanRead, RoutineCreate, RoutineRead, RoutineExerciseCreate
from app.db.models import Exercise # Ensure Exercise is imported
from app.schemas.plan import RoutineExerciseRead # Import the new schema

router = APIRouter(prefix="/plans", tags=["plans"])

from app.db.models import User
from app.core.security import get_current_user

# 1. LIST PLANS
@router.get("/", response_model=List[PlanRead])
def get_plans(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user) # <--- ADD THIS
):
    # Filter by user_id
    return session.exec(
        select(WorkoutPlan)
        .where(WorkoutPlan.is_active == True)
        .where(WorkoutPlan.user_id == current_user.id) # <--- FILTER
    ).all()

# 2. CREATE PLAN
@router.post("/", response_model=PlanRead)
def create_plan(
    plan_data: PlanCreate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user) # <--- ADD THIS
):
    start = plan_data.start_date
    end = start + timedelta(weeks=plan_data.duration_weeks)
    
    # Check overlap only for THIS user's plans
    statement = select(WorkoutPlan).where(
        WorkoutPlan.user_id == current_user.id, # <--- FILTER
        WorkoutPlan.is_active == True,
        col(WorkoutPlan.start_date) < end,
        col(WorkoutPlan.end_date) > start
    )
    conflicts = session.exec(statement).all()
    
    if conflicts:
        conflict_names = ", ".join([p.name for p in conflicts])
        raise HTTPException(
            status_code=400, 
            detail=f"Plan dates overlap with existing active plans: {conflict_names}"
        )

    db_plan = WorkoutPlan(
        name=plan_data.name,
        description=plan_data.description,
        duration_weeks=plan_data.duration_weeks,
        start_date=start,
        end_date=end,
        user_id=current_user.id # <--- ASSIGN OWNER
    )
    
    session.add(db_plan)
    session.commit()
    session.refresh(db_plan)
    
    return db_plan

# --- 3. GET PLAN DETAILS (Deep Read) ---
# Define response models locally or import them
class RoutineWithExercises(RoutineRead):
    exercises: List[RoutineExerciseRead]

class PlanDeepRead(PlanRead):
    routines: List[RoutineWithExercises]

@router.get("/{plan_id}", response_model=PlanDeepRead)
def get_plan_details(plan_id: uuid.UUID, session: Session = Depends(get_session)):
    plan = session.get(WorkoutPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
        
    routines = session.exec(select(WorkoutRoutine).where(WorkoutRoutine.plan_id == plan_id)).all()
    
    routines_data = []
    for r in routines:
        targets = session.exec(
            select(RoutineExercise)
            .where(RoutineExercise.routine_id == r.id)
            .order_by(RoutineExercise.order_index)
        ).all()
        
        exercises_list = []
        for t in targets:
            # Fetch the name for each target
            # (Optimization note: A JOIN query is faster, but this is clearer for now)
            ex_def = session.get(Exercise, t.exercise_id)
            
            exercises_list.append(RoutineExerciseRead(
                **t.model_dump(),
                name=ex_def.name if ex_def else "Unknown Exercise"
            ))

        routine_obj = RoutineWithExercises(
            **r.model_dump(), 
            exercises=exercises_list
        )
        routines_data.append(routine_obj)
        
    return PlanDeepRead(
        **plan.model_dump(),
        routines=routines_data
    )
# --- 4. DELETE PLAN ---
@router.delete("/{plan_id}")
def delete_plan(plan_id: uuid.UUID, session: Session = Depends(get_session)):
    plan = session.get(WorkoutPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    routines = session.exec(select(WorkoutRoutine).where(WorkoutRoutine.plan_id == plan_id)).all()
    routine_ids = [r.id for r in routines]
    
    has_history = False
    if routine_ids:
        count = session.exec(
            select(WorkoutSession)
            .where(col(WorkoutSession.routine_id).in_(routine_ids))
            .where(WorkoutSession.status == "completed")
        ).first()
        if count:
            has_history = True

    if has_history:
        plan.is_active = False
        session.add(plan)
        session.commit()
        return {"message": "Plan archived (history preserved)"}
    else:
        for r in routines:
            targets = session.exec(select(RoutineExercise).where(RoutineExercise.routine_id == r.id)).all()
            for t in targets: session.delete(t)
            session.delete(r)
        
        session.delete(plan)
        session.commit()
        return {"message": "Plan deleted permanently"}

# --- 5. SUB-RESOURCES ---
@router.post("/{plan_id}/routines", response_model=RoutineRead)
def add_routine(plan_id: uuid.UUID, routine_data: RoutineCreate, session: Session = Depends(get_session)):
    routine = WorkoutRoutine(
        plan_id=plan_id,
        name=routine_data.name,
        day_of_week=routine_data.day_of_week
    )
    session.add(routine)
    session.commit()
    session.refresh(routine)
    return routine

@router.post("/routines/{routine_id}/exercises", response_model=RoutineExerciseCreate)
def add_exercise_target(routine_id: uuid.UUID, target_data: RoutineExerciseCreate, session: Session = Depends(get_session)):
    routine = session.get(WorkoutRoutine, routine_id)
    if not routine:
        raise HTTPException(status_code=404, detail="Routine not found")
        
    target = RoutineExercise(
        routine_id=routine_id,
        exercise_id=target_data.exercise_id,
        order_index=target_data.order_index,
        target_sets=target_data.target_sets,
        target_reps=target_data.target_reps,
        target_weight=target_data.target_weight,
        rest_seconds=target_data.rest_seconds,
        increment_value=target_data.increment_value
    )
    session.add(target)
    session.commit()
    return target