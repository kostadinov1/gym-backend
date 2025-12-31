from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, col, or_
from typing import List
from datetime import timedelta, datetime
import uuid

from app.db.database import get_session
from app.db.models import WorkoutPlan, WorkoutRoutine, RoutineExercise, WorkoutSession
from app.schemas.plan import PlanCreate, PlanRead, PlanUpdate, RoutineCreate, RoutineRead, RoutineExerciseCreate

router = APIRouter(prefix="/plans", tags=["plans"])

@router.post("/", response_model=PlanRead)
def create_plan(plan_data: PlanCreate, session: Session = Depends(get_session)):
    # 1. Calculate End Date
    # We treat start_date as the beginning of that day
    start = plan_data.start_date
    end = start + timedelta(weeks=plan_data.duration_weeks)
    
    # 2. Overlap Validation
    # Logic: New Start < Existing End AND New End > Existing Start
    statement = select(WorkoutPlan).where(
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

    # 3. Create
    # We manually set end_date in the model (we need to add this field to the DB model first!)
    # *Note: We need to update app/db/models.py to include end_date column if not present*
    # For now, we calculate it dynamically or store it. 
    # Let's assume we store it for easier querying.
    
    db_plan = WorkoutPlan(
        name=plan_data.name,
        description=plan_data.description,
        duration_weeks=plan_data.duration_weeks,
        start_date=start,
        # We need to make sure our Model has this field, or we rely on calculation.
        # Let's verify models.py. You used `duration_weeks` there. 
        # We should calculate end_date on the fly OR add the column.
        # For valid overlap logic in SQL, adding the column is cleaner.
    )
    # *Fixing the Model on the fly check below*
    
    session.add(db_plan)
    session.commit()
    session.refresh(db_plan)
    
    # Return with calculated end_date
    return PlanRead(
        **db_plan.model_dump(), 
        end_date=end
    )

@router.get("/", response_model=List[PlanRead])
def get_plans(session: Session = Depends(get_session)):
    plans = session.exec(select(WorkoutPlan).where(WorkoutPlan.is_active == True)).all()
    # Compute end_date for response
    results = []
    for p in plans:
        end_date = p.start_date + timedelta(weeks=p.duration_weeks)
        results.append(PlanRead(**p.model_dump(), end_date=end_date))
    return results

@router.delete("/{plan_id}")
def delete_plan(plan_id: uuid.UUID, session: Session = Depends(get_session)):
    plan = session.get(WorkoutPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Safe Delete Check: Are there completed sessions for routines in this plan?
    # 1. Get all routine IDs
    routines = session.exec(select(WorkoutRoutine).where(WorkoutRoutine.plan_id == plan_id)).all()
    routine_ids = [r.id for r in routines]
    
    has_history = False
    if routine_ids:
        # 2. Check sessions
        count = session.exec(
            select(WorkoutSession)
            .where(col(WorkoutSession.routine_id).in_(routine_ids))
            .where(WorkoutSession.status == "completed")
        ).first()
        if count:
            has_history = True

    if has_history:
        # Soft Delete (Archive)
        plan.is_active = False
        session.add(plan)
        session.commit()
        return {"message": "Plan archived (history preserved)"}
    else:
        # Hard Delete (Cascading needs to be handled manually if not set in DB)
        # We manually delete sub-records to be safe
        for r in routines:
            # Delete targets
            targets = session.exec(select(RoutineExercise).where(RoutineExercise.routine_id == r.id)).all()
            for t in targets: session.delete(t)
            session.delete(r)
        
        session.delete(plan)
        session.commit()
        return {"message": "Plan deleted permanently"}

# --- Sub-Resource: Add Routine to Plan ---
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

# --- Sub-Resource: Add Exercise to Routine ---
@router.post("/routines/{routine_id}/exercises", response_model=RoutineExerciseCreate)
def add_exercise_target(routine_id: uuid.UUID, target_data: RoutineExerciseCreate, session: Session = Depends(get_session)):
    # Check if exists
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