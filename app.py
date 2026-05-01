"""
Wumpus World REST API
Flask server exposing game engine to the frontend
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from wumpus_engine import WumpusGame

app = Flask(__name__)
CORS(app)

# Single game session (for demo; extend with sessions for multi-user)
_game: WumpusGame = None


def _require_game():
    if _game is None:
        return jsonify({"error": "No game in progress. POST /api/new first."}), 400
    return None


@app.route("/api/new", methods=["POST"])
def new_game():
    global _game
    data = request.get_json(silent=True) or {}
    rows  = int(data.get("rows",  4))
    cols  = int(data.get("cols",  4))
    pits  = data.get("numPits", None)
    seed  = data.get("seed",    None)
    _game = WumpusGame(rows=rows, cols=cols, num_pits=pits, seed=seed)
    state = _game.reset()
    return jsonify(state)


@app.route("/api/state", methods=["GET"])
def get_state():
    err = _require_game()
    if err: return err
    return jsonify(_game.get_full_state())


@app.route("/api/move", methods=["POST"])
def move():
    err = _require_game()
    if err: return err
    data = request.get_json(silent=True) or {}
    direction = data.get("direction", "")
    state = _game.move(direction)
    return jsonify(state)


@app.route("/api/shoot", methods=["POST"])
def shoot():
    err = _require_game()
    if err: return err
    data = request.get_json(silent=True) or {}
    direction = data.get("direction", "")
    state = _game.shoot(direction)
    return jsonify(state)


@app.route("/api/climb", methods=["POST"])
def climb():
    err = _require_game()
    if err: return err
    return jsonify(_game.climb())


@app.route("/api/auto", methods=["POST"])
def auto_step():
    err = _require_game()
    if err: return err
    return jsonify(_game.auto_step())


@app.route("/api/reveal", methods=["GET"])
def reveal():
    err = _require_game()
    if err: return err
    return jsonify(_game.reveal_world())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)