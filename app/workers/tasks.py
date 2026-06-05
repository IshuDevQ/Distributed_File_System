from app.database import SessionLocal
from app.services.repair import repair_single_chunk, update_repair_task_status
from app.workers.celery_app import celery_app
from app.utils.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name="repair_chunk_task",
    max_retries=3,
    default_retry_delay=10
)
def repair_chunk_task(self, chunk_id: int) -> dict:
    db = SessionLocal()

    try:
        logger.info(f"Celery repair task started for chunk_id={chunk_id}")

        update_repair_task_status(
            db=db,
            chunk_id=chunk_id,
            status="running",
            message="Celery repair task running",
            task_id=self.request.id
        )

        result = repair_single_chunk(db, chunk_id)

        if result["status"] == "failed":
            raise RuntimeError(result["message"])

        return result

    except Exception as exc:
        db.rollback()

        try:
            update_repair_task_status(
                db=db,
                chunk_id=chunk_id,
                status="retrying",
                message=str(exc),
                task_id=self.request.id
            )
        except Exception:
            db.rollback()

        logger.warning(
            f"Repair task failed for chunk_id={chunk_id}, retrying: {exc}"
        )

        raise self.retry(exc=exc)

    finally:
        db.close()