import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.db.base import Base

# Import all models so Alembic can detect them
from app.modules.users.infrastructure.models import UserModel  # noqa: F401
from app.modules.user_profile.infrastructure.models import UserProfileModel  # noqa: F401
from app.modules.exercises.infrastructure.models import ExerciseModel  # noqa: F401
from app.modules.exercises.infrastructure.media_models import ExerciseMediaModel  # noqa: F401
from app.modules.muscle_groups.infrastructure.models import MuscleGroupModel  # noqa: F401
from app.modules.equipment.infrastructure.models import EquipmentModel  # noqa: F401
from app.modules.workout_plans.infrastructure.models import WorkoutPlanModel  # noqa: F401
from app.modules.workout_days.infrastructure.models import WorkoutDayModel  # noqa: F401
from app.modules.workout_exercises.infrastructure.models import WorkoutExerciseModel  # noqa: F401
from app.modules.workout_sessions.infrastructure.models import WorkoutSessionModel  # noqa: F401
from app.modules.workout_logs.infrastructure.models import WorkoutLogModel  # noqa: F401
from app.modules.progress.infrastructure.models import BodyProgressModel  # noqa: F401

# Alembic Config object
config = context.config

# Configure logging
if config.config_file_name:
    fileConfig(config.config_file_name)

# SQLAlchemy metadata
target_metadata = Base.metadata

# Set database URL dynamically from application settings
database_url = settings.get_database_url()
config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
