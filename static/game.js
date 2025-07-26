const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
const size = 20;
let snakes = [];
let fruit = null;

const ws = new WebSocket("ws://" + location.host + "/ws");

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "full") {
        alert("Сервер полон");
        return;
    }
    if (data.type === "update") {
        snakes = data.players;
        fruit = data.fruit;
    }
    if (data.winner !== null) {
    alert("Игрок " + (data.winner + 1) + " победил!");
    }
};

document.addEventListener("keydown", e => {
    const dirs = {
        "ArrowUp": {x: 0, y: -1},
        "ArrowDown": {x: 0, y: 1},
        "ArrowLeft": {x: -1, y: 0},
        "ArrowRight": {x: 1, y: 0}
    };
    if (dirs[e.key]) {
        ws.send(JSON.stringify({
            type: "dir",
            dir: dirs[e.key]
        }));
    }
});

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // змейки
    // внутри draw():
    snakes.forEach((p, index) => {
        const inv = p.invincible;
        if (!p.alive) return; // не рисуем мёртвых
        ctx.fillStyle = index === 0 ? "lime" : "red";
        p.snake.forEach(part => {
            if (inv) {
                // моргаем (пример)
                if (Math.floor(Date.now() / 200) % 2 === 0) {
                    ctx.globalAlpha = 0.3;
                } else {
                    ctx.globalAlpha = 1;
                }
            } else {
                ctx.globalAlpha = 1;
            }
            ctx.fillRect(part.x * size, part.y * size, size, size);
        });
        ctx.globalAlpha = 1;
    });

    // фрукт
    if (fruit) {
        ctx.fillStyle = "yellow";
        ctx.fillRect(fruit.x * size, fruit.y * size, size, size);
    }

    requestAnimationFrame(draw);
}
draw();
