const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");
const statusDiv = document.getElementById("status");

const size = 20; // размер клетки
const boardSize = 30;

let symbol = null;
let snake = [];
let otherSnake = [];
let fruit = null;
let gameRunning = false;

const socket = new WebSocket(`ws://${location.host}/ws`);

socket.onopen = () => {
    statusDiv.textContent = "Соединение установлено...";
};

socket.onmessage = (event) => {
    let data = JSON.parse(event.data);
    if(data.type === 'init') {
        symbol = data.symbol;
        statusDiv.textContent = `Ты игрок ${symbol}`;
    } else {
        // Получаем состояние игры
        if(data.game_running) {
            gameRunning = true;
            statusDiv.textContent = "Игра в процессе";
        } else {
            gameRunning = false;
            statusDiv.textContent = "Ожидание игроков...";
        }
        // Обновляем свои и чужие змейки
        if(symbol === 'X') {
            snake = data.players.X || [];
            otherSnake = data.players.O || [];
        } else if(symbol === 'O') {
            snake = data.players.O || [];
            otherSnake = data.players.X || [];
        }
        fruit = data.fruit;
        draw();
    }
};

socket.onclose = () => {
    statusDiv.textContent = "Соединение закрыто";
};

document.addEventListener("keydown", (e) => {
    if(!gameRunning) return;

    let dx = 0, dy = 0;
    if(e.key === "ArrowUp") { dx = 0; dy = -1; }
    else if(e.key === "ArrowDown") { dx = 0; dy = 1; }
    else if(e.key === "ArrowLeft") { dx = -1; dy = 0; }
    else if(e.key === "ArrowRight") { dx = 1; dy = 0; }
    else return;

    socket.send(JSON.stringify({dx, dy}));
});

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Рисуем фрукт
    if(fruit) {
        ctx.fillStyle = "red";
        ctx.fillRect(fruit.x * size, fruit.y * size, size, size);
    }

    // Рисуем свою змейку зелёным
    ctx.fillStyle = "lime";
    snake.forEach(p => ctx.fillRect(p.x * size, p.y * size, size, size));

    // Рисуем другую змейку красным
    ctx.fillStyle = "orange";
    otherSnake.forEach(p => ctx.fillRect(p.x * size, p.y * size, size, size));
}
