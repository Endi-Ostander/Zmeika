const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
const size = 20;
let snakes = [];
let fruit = null;
let extraFruits = [];
let connected = false;
let waiting = true;

const ws = new WebSocket((location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/ws");

ws.onopen = () => {
    connected = true;
    console.log("✅ WebSocket подключён");
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "full") {
        alert("Сервер полон");
        return;
    }

    if (data.type === "update") {
        snakes = data.players;
        fruit = data.fruit;
        extraFruits = data.extra_fruits || [];
        waiting = false;
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

// 👇 Простая передача направления (без KeyboardEvent)
function sendDir(x, y) {
    if (connected) {
        ws.send(JSON.stringify({
            type: "dir",
            dir: {x, y}
        }));
    }
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!connected) {
        ctx.fillStyle = "gray";
        ctx.font = "20px Arial";
        ctx.fillText("Подключение к серверу...", 50, 200);
    } else if (waiting) {
        ctx.fillStyle = "gray";
        ctx.font = "20px Arial";
        ctx.fillText("Ожидание второго игрока...", 50, 200);
    } else {
        snakes.forEach((p, index) => {
            const inv = p.invincible;
            if (!p.alive) return;
            ctx.fillStyle = index === 0 ? "lime" : "red";
            p.snake.forEach(part => {
                if (inv) {
                    ctx.globalAlpha = (Math.floor(Date.now() / 200) % 2 === 0) ? 0.3 : 1;
                } else {
                    ctx.globalAlpha = 1;
                }
                ctx.fillRect(part.x * size, part.y * size, size, size);
            });
            ctx.globalAlpha = 1;
        });

        // основной фрукт
        if (fruit) {
            ctx.fillStyle = "yellow";
            ctx.fillRect(fruit.x * size, fruit.y * size, size, size);
        }

        // фрукты от мёртвых змей
        ctx.fillStyle = "orange";
        extraFruits.forEach(f => {
            ctx.fillRect(f.x * size, f.y * size, size, size);
        });
    }

    requestAnimationFrame(draw);
}

draw();

