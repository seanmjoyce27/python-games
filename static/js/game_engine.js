/**
 * Simple Game Engine for Python Game Builder
 * Provides a bridge between Python (Pyodide) and HTML5 Canvas
 */

class GameEngine {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.running = false;
        this.animationId = null;
        this.fps = 60;
        this.frameTime = 1000 / this.fps;
        this.lastFrameTime = 0;

        // Game state from Python
        this.gameState = {
            objects: [],
            score: 0,
            gameOver: false,
            message: ''
        };

        // Input handling
        this.keys = {};
        this.setupInputHandlers();
    }

    setupInputHandlers() {
        window.addEventListener('keydown', (e) => {
            this.keys[e.key] = true;
            // Prevent arrow keys from scrolling
            if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' '].includes(e.key)) {
                e.preventDefault();
            }
        });

        window.addEventListener('keyup', (e) => {
            this.keys[e.key] = false;
        });
    }

    clear() {
        this.ctx.fillStyle = '#000000';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
    }

    drawRect(x, y, width, height, color = '#FFFFFF') {
        this.ctx.fillStyle = color;
        this.ctx.fillRect(x, y, width, height);
    }

    drawCircle(x, y, radius, color = '#FFFFFF') {
        this.ctx.fillStyle = color;
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius, 0, Math.PI * 2);
        this.ctx.fill();
    }

    drawText(text, x, y, size = 20, color = '#FFFFFF') {
        this.ctx.fillStyle = color;
        this.ctx.font = `${size}px Arial`;
        this.ctx.fillText(text, x, y);
    }

    // Update game state from Python
    updateGameState(stateJson) {
        try {
            this.gameState = JSON.parse(stateJson);
        } catch (e) {
            console.error('Error parsing game state:', e);
        }
    }

    // Render current game state
    render() {
        this.clear();

        // Draw all game objects
        for (const obj of this.gameState.objects) {
            switch (obj.type) {
                case 'rect':
                    this.drawRect(obj.x, obj.y, obj.width, obj.height, obj.color);
                    break;
                case 'circle':
                    this.drawCircle(obj.x, obj.y, obj.radius, obj.color);
                    break;
                case 'text':
                    this.drawText(obj.text, obj.x, obj.y, obj.size, obj.color);
                    break;
            }
        }

        // Draw score if present
        if (this.gameState.score !== undefined) {
            this.drawText(`Score: ${this.gameState.score}`, 10, 30, 24, '#FFFFFF');
        }

        // Draw message if present
        if (this.gameState.message) {
            const textWidth = this.ctx.measureText(this.gameState.message).width;
            const x = (this.canvas.width - textWidth) / 2;
            this.drawText(this.gameState.message, x, this.canvas.height / 2, 32, '#FF0000');
        }
    }

    // Check if a key is pressed
    isKeyPressed(key) {
        return this.keys[key] === true;
    }

    // Get all currently pressed keys
    getPressedKeys() {
        return Object.keys(this.keys).filter(k => this.keys[k]);
    }

    // Start game loop
    start(updateCallback) {
        this.running = true;
        this.updateCallback = updateCallback;
        this.lastFrameTime = performance.now();
        this.gameLoop();
    }

    // Stop game loop
    stop() {
        this.running = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }

    // Main game loop
    gameLoop = (timestamp) => {
        if (!this.running) return;

        // Calculate delta time
        const deltaTime = timestamp - this.lastFrameTime;

        // Only update if enough time has passed
        if (deltaTime >= this.frameTime) {
            this.lastFrameTime = timestamp - (deltaTime % this.frameTime);

            // Call Python update function
            if (this.updateCallback) {
                try {
                    this.updateCallback();
                } catch (e) {
                    console.error('Game update error:', e);
                    this.stop();
                    return;
                }
            }

            // Render frame
            this.render();
        }

        // Schedule next frame
        this.animationId = requestAnimationFrame(this.gameLoop);
    }
}

// Make GameEngine available globally
window.GameEngine = GameEngine;
