from fastapi import APIRouter
from app.api.v1.endpoints import health
from app.modules.users.presentation.routes import router as users_router
from app.modules.auth.presentation.routes import router as auth_router
from app.modules.user_profile.presentation.routes import router as profile_router
from app.modules.exercises.presentation.routes import router as exercises_router
from app.modules.muscle_groups.presentation.routes import router as muscle_groups_router
from app.modules.equipment.presentation.routes import router as equipment_router
from app.modules.workout_plans.presentation.routes import router as workout_plans_router
from app.modules.workout_days.presentation.routes import router as workout_days_router
from app.modules.workout_exercises.presentation.routes import router as workout_exercises_router
from app.modules.workout_sessions.presentation.routes import router as workout_sessions_router
from app.modules.workout_logs.presentation.routes import router as workout_logs_router
from app.modules.progress.presentation.routes import router as progress_router

api_router = APIRouter()

# Mount endpoints
api_router.include_router(health.router)
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(profile_router, prefix="/profile", tags=["User Profile"])
api_router.include_router(exercises_router, prefix="/exercises", tags=["Exercises"])
api_router.include_router(muscle_groups_router, prefix="/muscle-groups", tags=["Muscle Groups"])
api_router.include_router(equipment_router, prefix="/equipment", tags=["Equipment"])
api_router.include_router(workout_plans_router, prefix="/workout-plans", tags=["Workout Plans"])
api_router.include_router(workout_days_router, prefix="", tags=["Workout Days"])
api_router.include_router(workout_exercises_router, prefix="", tags=["Workout Exercises"])
api_router.include_router(workout_sessions_router, prefix="/workout-sessions", tags=["Workout Sessions"])
api_router.include_router(workout_logs_router, prefix="", tags=["Workout Logs"])
api_router.include_router(progress_router, prefix="/progress", tags=["Body Progress"])
