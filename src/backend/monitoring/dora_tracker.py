
import os
import psycopg2
import logging
from datetime import datetime
import json
from enum import Enum

logger = logging.getLogger(__name__)

class MetricType(str, Enum):
    DEPLOYMENT = "deployment"
    LEAD_TIME = "lead_time"
    FAILURE = "failure" # or 'change_failure'
    RESTORE = "restore" # Time to restore service

class IncidentStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"

class DoraTracker:
    """
    Utility to record DORA metrics and manage incidents.
    Intended to be used by CI/CD scripts, backend services, or manual triggers.
    """
    
    def __init__(self):
        self.db_host = os.getenv("POSTGRES_HOST", "shared-db") # Default internal docker name
        self.db_name = os.getenv("POSTGRES_DB", "postgres")
        self.db_user = os.getenv("POSTGRES_USER", "postgres")
        self.db_password = os.getenv("POSTGRES_PASSWORD", "postgres")
        
    def _get_connection(self):
        try:
            return psycopg2.connect(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
        except Exception as e:
            logger.error(f"Failed to connect to DB for metrics: {e}")
            return None

    def record_deployment(self, version: str, commit_sha: str = None, component: str = "backend"):
        """
        Record a successful deployment event.
        Also used to calculate frequency.
        """
        self._record_metric(
            metric_type=MetricType.DEPLOYMENT,
            value=1.0, # Count event
            metadata={
                "version": version,
                "commit_sha": commit_sha,
                "component": component
            }
        )
        logger.info(f"Recorded deployment for {component}:{version}")

    def record_lead_time(self, lead_time_minutes: float, commit_sha: str, version: str):
        """
        Record the lead time for a change (commit to deploy).
        """
        self._record_metric(
            metric_type=MetricType.LEAD_TIME,
            value=lead_time_minutes,
            metadata={
                "commit_sha": commit_sha,
                "version": version
            }
        )
        
    def record_change_failure(self, version: str, description: str, component: str = "backend"):
        """
        Record a deployment failure (adds to change failure rate).
        """
        self._record_metric(
            metric_type=MetricType.FAILURE,
            value=1.0,
            metadata={
                "version": version,
                "description": description,
                "component": component
            }
        )
        logger.warning(f"Recorded change failure for {component}:{version}")

    def _record_metric(self, metric_type: str, value: float, metadata: dict = None):
        conn = self._get_connection()
        if not conn:
            return
            
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO dora_metrics (metric_type, value, metadata, timestamp)
                    VALUES (%s, %s, %s, NOW())
                    """,
                    (metric_type, value, json.dumps(metadata or {}))
                )
            conn.commit()
        except Exception as e:
            logger.error(f"Error recording metric {metric_type}: {e}")
        finally:
            conn.close()

    # --- Incident Management (MTTR) ---

    def start_incident(self, service: str, description: str, severity: str = "medium") -> int:
        """
        Create a new incident. Returns incident_id.
        """
        conn = self._get_connection()
        if not conn:
            return -1
            
        incident_id = -1
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO dora_incidents (service, description, severity, status, start_time)
                    VALUES (%s, %s, %s, %s, NOW())
                    RETURNING id
                    """,
                    (service, description, severity, IncidentStatus.OPEN)
                )
                incident_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"Started incident #{incident_id} for {service}")
        except Exception as e:
            logger.error(f"Error creating incident: {e}")
        finally:
            conn.close()
        return incident_id

    def resolve_incident(self, incident_id: int):
        """
        Mark incident as resolved and record MTTR metric.
        """
        conn = self._get_connection()
        if not conn:
            return
            
        try:
            mttr_minutes = 0
            with conn.cursor() as cur:
                # Close incident
                cur.execute(
                    """
                    UPDATE dora_incidents 
                    SET 
                        status = %s,
                        end_time = NOW()
                    WHERE id = %s AND status = %s
                    RETURNING start_time, end_time
                    """,
                    (IncidentStatus.RESOLVED, incident_id, IncidentStatus.OPEN)
                )
                row = cur.fetchone()
                if row:
                    start, end = row
                    delta = end - start
                    mttr_minutes = delta.total_seconds() / 60.0
                else:
                    logger.warning(f"Incident {incident_id} not found or already closed")
                    return

            conn.commit()
            
            if mttr_minutes > 0:
                # Record MTTR metric automatically
                self._record_metric(
                    metric_type=MetricType.RESTORE,
                    value=mttr_minutes,
                    metadata={"incident_id": incident_id}
                )
                logger.info(f"Resolved incident #{incident_id}. MTTR: {mttr_minutes:.2f} min")
                
        except Exception as e:
            logger.error(f"Error resolving incident {incident_id}: {e}")
        finally:
            conn.close()
