from flask import Flask, send_from_directory
from flask_sock import Sock
import random, time, threading, json, os
import eventlet
eventlet.monkey_patch()

app = Flask(__name__, static_folder='static')
sock = Sock(app)

players = []
fruit = {"x": 10, "y": 10}
board_size = 30
respawn_time = 3
invincible_time = 3
target_length = 30

def new_snake():
    return [{"x": 5, "y": 5}, {"x": 4, "y": 5}]

def random_fruit():
    return {"x": random.randint(0, board_size - 1), "y": random.randint(0, board_size - 1)}

def wrap_position(pos):
    return {
        "x": pos["x"] % board_size,
        "y": pos["y"] % board_size
    }

def is_collision(head, body):
    return any(part["x"] == head["x"] and part["y"] == head["y"] for part in body)

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("static", path)

@sock.route('/ws')
def websocket(ws):
    if len(players) >= 2:
        ws.send(json.dumps({"type": "full"}))
        return

    player = {
        "ws": ws,
        "snake": new_snake(),
        "dir": {"x": 1, "y": 0},
        "alive": True,
        "respawn_timer": 0,
        "invincible_timer": time.time() + invincible_time
    }
    players.append(player)

    try:
        while True:
            msg = ws.receive()
            if not msg:
                break
            data = json.loads(msg)
            if data["type"] == "dir":
                dx, dy = data["dir"]["x"], data["dir"]["y"]
                cur_dx, cur_dy = player["dir"]["x"], player["dir"]["y"]
                if (dx, dy) != (-cur_dx, -cur_dy):
                    player["dir"] = {"x": dx, "y": dy}
    except:
        pass
    finally:
        if player in players:
            players.remove(player)

def game_loop():
    global fruit
    while True:
        now = time.time()
        winner = None

        if len(players) == 2:
            for p in players:
                if not p["alive"]:
                    if now >= p["respawn_timer"]:
                        p["alive"] = True
                        p["snake"] = new_snake()
                        p["dir"] = {"x": 1, "y": 0}
                        p["invincible_timer"] = now + invincible_time
                    continue

                dx, dy = p["dir"]["x"], p["dir"]["y"]
                head = wrap_position({
                    "x": p["snake"][0]["x"] + dx,
                    "y": p["snake"][0]["y"] + dy
                })

                # Проверка на столкновения
                others = [pl for pl in players if pl != p and pl["alive"]]
                other_body = []
                for o in others:
                    other_body.extend(o["snake"])

                own_body = p["snake"][1:]
                invincible = p["invincible_timer"] > now

                if not invincible and is_collision(head, own_body + other_body):
                    p["alive"] = False
                    p["respawn_timer"] = now + respawn_time
                    continue

                p["snake"].insert(0, head)

                if head["x"] == fruit["x"] and head["y"] == fruit["y"]:
                    fruit = random_fruit()
                else:
                    p["snake"].pop()

                # Победа
                if len(p["snake"]) >= target_length:
                    winner = p

            for p in players:
                try:
                    p["ws"].send(json.dumps({
                        "type": "update",
                        "players": [{
                            "snake": pl["snake"],
                            "alive": pl["alive"],
                            "invincible": pl["invincible_timer"] > now
                        } for pl in players],
                        "fruit": fruit,
                        "winner": players.index(winner) if winner else None
                    }))
                except:
                    pass

        time.sleep(0.15)

threading.Thread(target=game_loop, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
