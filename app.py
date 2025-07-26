from flask import Flask, send_from_directory
from flask_sock import Sock
import random, time, threading, json

app = Flask(__name__, static_folder='static')
sock = Sock(app)

players = []
fruit = {"x": 10, "y": 10}
board_size = 30
respawn_time = 3  # секунды до возрождения
invincible_time = 3  # секунды неуязвимости после респавна
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

def is_collision(head, snakes):
    for part in snakes:
        if part["x"] == head["x"] and part["y"] == head["y"]:
            return True
    return False

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
        "invincible_timer": 0
    }
    players.append(player)

    try:
        while True:
            msg = ws.receive()
            if not msg:
                break
            data = json.loads(msg)
            if data["type"] == "dir":
                # Запрещаем менять направление в противоположную сторону
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
        if len(players) == 2:
            for p in players:
                if not p["alive"]:
                    # Обработка респавна
                    if now >= p["respawn_timer"]:
                        p["alive"] = True
                        p["snake"] = new_snake()
                        p["invincible_timer"] = now + invincible_time
                        p["dir"] = {"x": 1, "y": 0}
                    continue

                snake = p["snake"]
                dx, dy = p["dir"]["x"], p["dir"]["y"]
                head = {"x": snake[0]["x"] + dx, "y": snake[0]["y"] + dy}
                head = wrap_position(head)

                # Собираем тела всех змей кроме головы текущей
                other_snakes = [pl for pl in players if pl != p and pl["alive"]]
                other_bodies = []
                for pl in other_snakes:
                    other_bodies.extend(pl["snake"])
                own_body = snake[1:]  # без головы
                collision_bodies = other_bodies + own_body

                # Проверяем столкновение, учитывая неуязвимость
                invincible = p["invincible_timer"] > now

                if not invincible and is_collision(head, collision_bodies):
                    # смерть
                    p["alive"] = False
                    p["respawn_timer"] = now + respawn_time
                    continue

                snake.insert(0, head)

                # Проверка сбора фрукта
                if head["x"] == fruit["x"] and head["y"] == fruit["y"]:
                    fruit = random_fruit()
                    # цель - длина 30, игра можно закончить или что-то сделать, пока просто растём
                else:
                    snake.pop()

            # Отправляем обновления
            for p in players:
                try:
                    p["ws"].send(json.dumps({
                        "type": "update",
                        "players": [{
                            "snake": pl["snake"],
                            "alive": pl["alive"],
                            "invincible": pl["invincible_timer"] > now
                        } for pl in players],
                        "fruit": fruit
                    }))
                except:
                    pass

        time.sleep(0.15)

threading.Thread(target=game_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=True)
