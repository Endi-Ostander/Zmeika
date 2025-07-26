from quart import Quart, websocket, send_from_directory
import asyncio
import random, time, json

app = Quart(__name__, static_folder='static')

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
    return {"x": pos["x"] % board_size, "y": pos["y"] % board_size}

def is_collision(head, body):
    return any(part["x"] == head["x"] and part["y"] == head["y"] for part in body)

@app.route("/")
async def index():
    return await send_from_directory("static", "index.html")

@app.route("/<path:path>")
async def static_files(path):
    return await send_from_directory("static", path)

@app.websocket("/ws")
async def ws():
    if len(players) >= 2:
        await websocket.send(json.dumps({"type": "full"}))
        return

    player = {
        "ws": websocket,
        "snake": new_snake(),
        "dir": {"x": 1, "y": 0},
        "alive": True,
        "respawn_timer": 0,
        "invincible_timer": asyncio.get_event_loop().time() + invincible_time
    }
    players.append(player)

    try:
        while True:
            msg = await websocket.receive()
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

async def game_loop():
    global fruit
    while True:
        now = asyncio.get_event_loop().time()
        winner = None

        if len(players) >= 1:
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

                if len(p["snake"]) >= target_length and all(pl["alive"] for pl in players):
                    winner = p

            for p in players:
                try:
                    await p["ws"].send(json.dumps({
                        "type": "update",
                        "players": [{
                            "snake": pl["snake"],
                            "alive": pl["alive"],
                            "invincible": pl["invincible_timer"] > now
                        } for pl in players],
                        "fruit": fruit,
                        "winner": players.index(winner) if winner in players else None
                    }))
                except:
                    pass

        await asyncio.sleep(0.15)

@app.before_serving
async def startup():
    app.add_background_task(game_loop)

if __name__ == "__main__":
    import os
    from hypercorn.asyncio import serve
    from hypercorn.config import Config
    import asyncio

    port = int(os.environ.get("PORT", 5000))
    config = Config()
    config.bind = [f"0.0.0.0:{port}"]

    asyncio.run(serve(app, config))
