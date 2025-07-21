// Canvas fallback for NERV when Konva fails
class CanvasFallback {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.points = [];
    
    // Set canvas size
    this.canvas.width = this.canvas.parentElement.clientWidth - 2;
    this.canvas.height = this.canvas.parentElement.clientHeight - 2;
    
    // Set up event listeners
    this.canvas.addEventListener('click', (e) => this.handleClick(e));
    
    this.drawGrid();
  }
  
  drawGrid() {
    const ctx = this.ctx;
    const gridSize = 20;
    
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 0.5;
    
    // Draw vertical lines
    for (let x = 0; x <= this.canvas.width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, this.canvas.height);
      ctx.stroke();
    }
    
    // Draw horizontal lines
    for (let y = 0; y <= this.canvas.height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(this.canvas.width, y);
      ctx.stroke();
    }
  }
  
  handleClick(e) {
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    this.addPoint(x, y);
  }
  
  addPoint(x, y) {
    this.points.push({x, y});
    
    // Draw point
    const ctx = this.ctx;
    ctx.fillStyle = '#00ff00';
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, 2 * Math.PI);
    ctx.fill();
    
    // Add label
    ctx.fillStyle = '#ffffff';
    ctx.font = '12px Courier New';
    ctx.fillText(`P${this.points.length}`, x + 8, y - 8);
    
    console.log(`Point added at (${x.toFixed(1)}, ${y.toFixed(1)})`);
  }
  
  clear() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.points = [];
    this.drawGrid();
  }
}