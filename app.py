from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
import random

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# HTML просто редирект на index.html
html = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Мультиплеер Змейка</title></head>
<body>
<script>window.location.href="/static/index.html";</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return html

# Игровые данные
BOARD_SIZE = 30

class Player:
    def __init__(self, websocket: WebSocket, symbol: str):
        self.websocket = websocket
        self.symbol = symbol
        self.snake = [{'x': 5, 'y': 5}] if symbol == 'X' else [{'x': 24, 'y': 24}]
        self.dir = {'x': 1, 'y': 0}
        self.alive = True

players = {}  # symbol -> Player
fruit = None
game_running = False

async def broadcast_state():
    state = {
        'players': {
            sym: p.snake for sym, p in players.items()
        },
        'fruit': fruit,
        'game_running': game_running
    }
    # Отправляем всем подключенным игрокам
    for p in players.values():
        await p.websocket.send_json(state)

def random_fruit():
    while True:
        pos = {'x': random.randint(0, BOARD_SIZE-1), 'y': random.randint(0, BOARD_SIZE-1)}
        # Проверяем чтобы фрукт не на змейках
        if all(pos not in p.snake for p in players.values()):
            return pos

async def game_loop():
    global fruit, game_running
    while game_running:
        # Обновляем змей игроков
        for p in players.values():
            if not p.alive:
                continue
            head = {'x': p.snake[0]['x'] + p.dir['x'], 'y': p.snake[0]['y'] + p.dir['y']}
            # Проверка выхода за границы
            if head['x'] < 0 or head['x'] >= BOARD_SIZE or head['y'] < 0 or head['y'] >= BOARD_SIZE:
                p.alive = False
                continue
            # Проверка столкновения с собой
            if head in p.snake:
                p.alive = False
                continue
            # Проверка столкновения с другой змейкой
            other = [pos for other_p in players.values() if other_p != p for pos in other_p.snake]
            if head in other:
                p.alive = False
                continue

            p.snake.insert(0, head)

            # Проверка съедания фрукта
            if fruit and head == fruit:
                fruit = random_fruit()  # Новый фрукт
            else:
                p.snake.pop()  # Удаляем хвост если фрукт не съеден

        # Если все игроки мертвы - остановить игру
        if all(not p.alive for p in players.values()):
            game_running = False

        await broadcast_state()
        await asyncio.sleep(0.2)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global fruit, game_running
    await websocket.accept()

    # Ограничим до 2 игроков X и O
    if 'X' not in players:
        symbol = 'X'
    elif 'O' not in players:
        symbol = 'O'
    else:
        await websocket.send_text("Игра полна")
        await websocket.close()
        return

    player = Player(websocket, symbol)
    players[symbol] = player

    # Если два игрока - запускаем игру
    if len(players) == 2 and not game_running:
        fruit = random_fruit()
        game_running = True
        asyncio.create_task(game_loop())

    try:
        await websocket.send_json({'type': 'init', 'symbol': symbol})
        while True:
            data = await websocket.receive_json()
            # Принимаем направление движения
            dx = data.get('dx')
            dy = data.get('dy')
            if dx is not None and dy is not None:
                # Не даём разворачиваться назад
                if not (dx == -player.dir['x'] and dy == -player.dir['y']):
                    player.dir = {'x': dx, 'y': dy}

    except WebSocketDisconnect:
        del players[symbol]
        # Остановить игру если игроков меньше 2
        game_running = False

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
