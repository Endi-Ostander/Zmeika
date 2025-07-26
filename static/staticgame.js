const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");
const protocol = location.protocol === "https:" ? "wss:" : "ws:";
const socket = new WebSocket(`${protocol}//${location.host}/ws`);


const size = 20;
let snake = [{x: 3, y: 3}];
let dir = {x: 1, y: 0};

let otherSnake = [];

socket.onmessage = (event) => {
    otherSnake = JSON.parse(event.data);
};

document.addEventListener("keydown", (e) => {
    if (e.key === "ArrowUp") dir = {x: 0, y: -1};
    if (e.key === "ArrowDown") dir = {x: 0, y: 1};
    if (e.key === "ArrowLeft") dir = {x: -1, y: 0};
    if (e.key === "ArrowRight") dir = {x: 1, y: 0};
});

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = "lime";
    snake.forEach(p => ctx.fillRect(p.x * size, p.y * size, size, size));
    ctx.fillStyle = "red";
    otherSnake.forEach(p => ctx.fillRect(p.x * size, p.y * size, size, size));
}

function update() {
    const head = {x: snake[0].x + dir.x, y: snake[0].y + dir.y};
    snake.unshift(head);
    snake.pop();
    socket.send(JSON.stringify(snake));
}

setInterval(() => {
    update();
    draw();
}, 200);