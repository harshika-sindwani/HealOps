import docker
import time
from datetime import datetime

client = docker.from_env()

TARGET_CONTAINER = "healops-backend"
CHECK_INTERVAL = 3
COOLDOWN = 30
MAX_RETRIES = 3

last_restart = 0
restart_attempts = 0


def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def recover(container):
    global last_restart, restart_attempts

    if time.time() - last_restart < COOLDOWN:
        log("Recovery cooldown active.")
        return

    if restart_attempts >= MAX_RETRIES:
        log("CRITICAL: Maximum recovery attempts reached!")
        return

    restart_attempts += 1
    last_restart = time.time()

    log(f"Recovery attempt {restart_attempts}/{MAX_RETRIES}")
    log("Initiating recovery...")

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
                log("SUCCESS: Container recovered!")
                restart_attempts = 0
                return

        log("WARNING: Recovery initiated but health not verified.")

    except Exception as error:
        log(f"RECOVERY FAILED: {error}")


def monitor():
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

            if state != "running" or health == "unhealthy":
                log("FAILURE DETECTED!")
                recover(container)

        except docker.errors.NotFound:
            log("CRITICAL: Target container not found.")

        except Exception as error:
            log(f"MONITORING ERROR: {error}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    monitor()