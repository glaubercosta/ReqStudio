"""Alembic migration runner for application startup.

Executes ``alembic upgrade head`` synchronously before the API begins
accepting requests.  Skipped entirely in test environments.
"""

import logging
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import settings

logger = logging.getLogger(__name__)


def _get_alembic_config() -> Config:
    """Return an Alembic Config pointing to the project-root alembic.ini.

    Layout inside the container::

        /app/                ← WORKDIR / project root
            alembic.ini
            alembic/
            app/
                db/
                    migrations.py   ← __file__
    """
    # Two parents up from app/db → app/ → project root
    root = Path(__file__).resolve().parent.parent.parent
    alembic_ini = root / "alembic.ini"
    return Config(str(alembic_ini))


def run_migrations_on_startup() -> None:
    """Run ``alembic upgrade head`` at application startup.

    Behaviour:
    - **Test environment** (``settings.TESTING is True``): skipped.
    - **Success**: logs INFO at start and finish.
    - **Failure**: logs CRITICAL with full traceback and calls
      ``sys.exit(1)`` so the container exits with a non-zero code,
      which signals Docker / Kubernetes that the pod is unhealthy.
    """
    if settings.TESTING:
        logger.info("Skipping Alembic migrations in test environment")
        return

    logger.info("Running Alembic migrations...")
    try:
        cfg = _get_alembic_config()
        command.upgrade(cfg, "head")
        logger.info("Alembic migrations complete")
    except Exception as exc:  # noqa: BLE001 — intentional catch-all at boundary
        logger.critical(
            "Alembic migration failed — aborting startup: %s",
            exc,
            exc_info=True,
        )
        sys.exit(1)
