import docker
import time

client = docker.from_env()

TARGET_CONTAINER = "healops-backend"
CHECK_INTERVAL = 3
COOLDOWN = 30

last_restart = 0

print("HealOps Healing Engine Started!")

while True:
    try:
        container = client.containers.get(TARGET_CONTAINER)
        container.reload()

        health = container.attrs.get("State", {}).get(
            "Health", {}
        ).get("Status", "unknown")

        print(f"Backend health: {health}")

        if health == "unhealthy":
            current_time = time.time()

            if current_time - last_restart >= COOLDOWN:
                print("Failure detected!")
                print("Initiating automatic recovery...")

                container.restart(timeout=5)
                last_restart = current_time

                print("Recovery initiated successfully!")

            else:
                print("Recovery cooldown active.")

    except docker.errors.NotFound:
        print("Target container not found.")

    except Exception as error:
        print(f"Healing engine error: {error}")

    time.sleep(CHECK_INTERVAL)