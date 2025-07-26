from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import random
import asyncio
import json

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Multiplayer Snake</title>
</head>
<body>
<script>
    window.location.href = "/static/index.html";
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return html

players = []
fruit = {"x": random.randint(0, 29), "y": random.randint(0, 29)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    if len(players) >= 2:
        await websocket.send_text(json.dumps({"type": "full"}))
        await websocket.close()
        return

    player_id = len(players)
    players.append({"ws": websocket, "id": player_id, "snake": [{"x": 5+5*player_id, "y": 5}], "dir": {"x": 0, "y": 0}})
    
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            if payload["type"] == "dir":
                players[player_id]["dir"] = payload["dir"]
    except WebSocketDisconnect:
        players.remove(players[player_id])

async def game_loop():
    while True:
        await asyncio.sleep(0.2)
        if len(players) < 2:
            continue
        
        # Обновление змей
        for player in players:
            snake = player["snake"]
            direction = player["dir"]
            if direction["x"] == 0 and direction["y"] == 0:
                continue
            new_head = {
                "x": snake[0]["x"] + direction["x"],
                "y": snake[0]["y"] + direction["y"]
            }

            # Проверка на съедение фрукта
            if new_head["x"] == fruit["x"] and new_head["y"] == fruit["y"]:
                snake.insert(0, new_head)
                fruit["x"] = random.randint(0, 29)
                fruit["y"] = random.randint(0, 29)
            else:
                snake.insert(0, new_head)
                snake.pop()

        # Отправка состояния
        state = {
            "type": "update",
            "players": [
                {"id": p["id"], "snake": p["snake"]}
                for p in players
            ],
            "fruit": fruit
        }

        for player in players:
            try:
                await player["ws"].send_text(json.dumps(state))
            except:
                pass

import threading

@app.on_event("startup")
async def on_startup():
    loop = asyncio.get_event_loop()
    loop.create_task(game_loop())

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=10000)
