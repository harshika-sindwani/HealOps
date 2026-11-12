import docker
import time

from incident_logger import initialize_database, record_incident

client = docker.from_env()

TARGET_CONTAINER = "healops-backend"
CHECK_INTERVAL = 3
COOLDOWN = 30
MAX_RETRIES = 3

last_restart = 0
restart_attempts = 0


def log(message):
    print(f"[HEALOPS] {message}", flush=True)


def recover(container, failure_type):
    global last_restart, restart_attempts

    if time.time() - last_restart < COOLDOWN:
        log("Recovery cooldown active.")
        return

    if restart_attempts >= MAX_RETRIES:
        log("CRITICAL: Maximum recovery attempts reached.")
        return

    restart_attempts += 1
    attempts_for_incident = restart_attempts
    last_restart = time.time()

    start_time = time.monotonic()
    recovery_status = "failed"
    recovery_action = "Container restart"

    log(f"Recovery attempt {attempts_for_incident}/{MAX_RETRIES}")
    log("Initiating automatic recovery...")

    try:
        container.restart(timeout=5)

        for _ in range(15):
            time.sleep(2)
            container.reload()

            state = container.attrs["State"]["Status"]
            health = container.attrs["State"].get(
                "Health", {}
            ).get("Status", "unknown")

            if state == "running" and health == "healthy":
                recovery_status = "recovered"
                log("SUCCESS: Container recovered!")
                restart_attempts = 0
                break

        if recovery_status != "recovered":
            log("WARNING: Recovery initiated but health not verified.")

    except Exception as error:
        log(f"RECOVERY FAILED: {error}")

    duration = round(time.monotonic() - start_time, 2)

    try:
        record_incident(
            container_name=TARGET_CONTAINER,
            failure_type=failure_type,
            recovery_action=recovery_action,
            duration=duration,
            status=recovery_status,
            attempts=attempts_for_incident
        )
        log("Incident saved to PostgreSQL.")

    except Exception as error:
        log(f"Incident logging failed: {error}")


def monitor():
    initialize_database()

    log("===================================")
    log("       HEALOPS ENGINE STARTED")
    log("===================================")

    while True:
        try:
            container = client.containers.get(TARGET_CONTAINER)
            container.reload()

            state = container.attrs["State"]["Status"]
            health = container.attrs["State"].get(
                "Health", {}
            ).get("Status", "unknown")

            log(f"Container: {state} | Health: {health}")

            if state != "running":
                log("FAILURE DETECTED: Container stopped!")
                recover(container, "container_stopped")

            elif health == "unhealthy":
                log("FAILURE DETECTED: Application unhealthy!")
                recover(container, "application_unhealthy")

        except docker.errors.NotFound:
            log("CRITICAL: Target container not found.")

        except Exception as error:
            log(f"MONITORING ERROR: {error}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    monitor()