
from flask import Flask, jsonify

app = Flask(__name__)

# Simulated application failure
failing = False


@app.route("/")
def home():
    return jsonify({
        "application": "HealOps",
        "message": "Backend is running!"
    })


@app.route("/health")
def health():
    if failing:
        return jsonify({"status": "unhealthy"}), 500

    return jsonify({"status": "healthy"}), 200


@app.route("/fail", methods=["POST"])
def simulate_failure():
    global failing
    failing = True

    return jsonify({
        "message": "Failure simulated successfully"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
