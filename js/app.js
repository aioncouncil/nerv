/**
 * NERV - Neural Euclidean Reconstruction Vessel
 * Interactive Geometric Construction Interface
 * 
 * This application provides a real-time geometric construction environment
 * with AI assistance, element collection, and validation through the NERV API.
 */

class NERVApp {
  constructor() {
    this.apiBaseUrl = 'http://localhost:8001/api/v1';
    this.currentTool = 'point';
    this.selectedMagi = 'casper';
    this.constructionSpace = {
      points: {},
      lines: {},
      circles: {},
      history: []
    };
    this.playerCollection = null;
    this.stage = null;
    this.layer = null;
    this.isApiConnected = false;
    
    // Drawing state
    this.drawingState = {
      isDrawing: false,
      startPoint: null,
      tempObjects: [],
      snapDistance: 10
    };
    
    this.init().catch(error => {
      console.error('❌ NERV initialization failed:', error);
      this.showNotification('Initialization failed: ' + error.message, 'error');
    });
  }
  
  async init() {
    console.log('🚀 Initializing NERV Interface...');
    
    // Initialize Konva stage
    this.initCanvas();
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Connect to API
    await this.connectToAPI();
    
    // Load player collection
    await this.loadPlayerCollection();
    
    // Start system status updates
    this.startStatusUpdates();
    
    console.log('✅ NERV Interface ready');
    this.showNotification('NERV system online', 'success');
  }
  
  initCanvas() {
    try {
      console.log('📐 Initializing Konva canvas...');
      
      const container = document.getElementById('geometryCanvas');
      if (!container) {
        throw new Error('Canvas container not found');
      }
      
      const containerRect = container.parentElement.getBoundingClientRect();
      console.log(`📏 Container dimensions: ${containerRect.width}x${containerRect.height}`);
      
      // Ensure minimum size
      const width = Math.max(containerRect.width - 2, 400);
      const height = Math.max(containerRect.height - 2, 300);
      
      this.stage = new Konva.Stage({
        container: 'geometryCanvas',
        width: width,
        height: height,
      });
      
      console.log(`🎭 Stage created: ${this.stage.width()}x${this.stage.height()}`);
      
      this.layer = new Konva.Layer();
      this.stage.add(this.layer);
      
      console.log(`🍰 Layer created and added to stage`);
      
      // Add grid background
      this.addGrid();
      
      // Canvas event listeners
      this.stage.on('click', (e) => {
        console.log('🖱️ Stage click event triggered');
        this.handleCanvasClick(e);
      });
      
      this.stage.on('mousemove', (e) => this.handleCanvasMove(e));
      this.stage.on('contextmenu', (e) => {
        e.evt.preventDefault();
        this.handleRightClick(e);
      });
      
      
      // Resize handler
      window.addEventListener('resize', () => this.resizeCanvas());
      
      console.log('✅ Konva canvas initialized successfully');
      this.showNotification('Canvas ready - click to place points! Red test dot should be visible.', 'success');
      
    } catch (error) {
      console.error('❌ Konva canvas initialization failed:', error);
      console.error('❌ Error details:', error.message);
      this.initFallbackCanvas();
    }
  }
  
  initFallbackCanvas() {
    try {
      console.log('🔄 Initializing fallback canvas...');
      
      // Replace canvas element with regular HTML5 canvas
      const container = document.getElementById('geometryCanvas');
      container.innerHTML = '<canvas id="fallback-canvas" style="background: #111; border: 1px solid #333;"></canvas>';
      
      this.fallbackCanvas = new CanvasFallback('fallback-canvas');
      this.useFallback = true;
      
      console.log('✅ Fallback canvas initialized');
      this.showNotification('Canvas ready (simplified mode) - click to place points!', 'warning');
      
    } catch (error) {
      console.error('❌ Fallback canvas also failed:', error);
      this.showNotification('Canvas initialization failed completely', 'error');
      
      // Last resort - show instructions
      const container = document.getElementById('geometryCanvas');
      container.innerHTML = '<div style="color: red; padding: 20px; text-align: center;">Canvas failed to load.<br>Please refresh the page.</div>';
    }
  }
  
  addGrid() {
    const width = this.stage.width();
    const height = this.stage.height();
    const majorGridSize = 40;  // Fewer, larger grid squares
    
    const gridGroup = new Konva.Group({ id: 'grid' });
    
    // Major vertical lines only
    for (let x = 0; x <= width; x += majorGridSize) {
      gridGroup.add(new Konva.Line({
        points: [x, 0, x, height],
        stroke: 'rgba(0, 255, 255, 0.15)',
        strokeWidth: 0.5,
        listening: false
      }));
    }
    
    // Major horizontal lines only  
    for (let y = 0; y <= height; y += majorGridSize) {
      gridGroup.add(new Konva.Line({
        points: [0, y, width, y],
        stroke: 'rgba(0, 255, 255, 0.15)',
        strokeWidth: 0.5,
        listening: false
      }));
    }
    
    this.layer.add(gridGroup);
    gridGroup.moveToBottom();
  }
  
  setupEventListeners() {
    // Tool buttons
    document.querySelectorAll('.tool-button').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const tool = e.target.dataset.tool;
        if (tool) this.selectTool(tool);
      });
    });
    
    // MAGI tabs
    document.querySelectorAll('.magi-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        this.selectMagi(e.target.dataset.magi);
      });
    });
    
    // MAGI input
    document.getElementById('magi-input').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this.sendToMagi();
    });
    
    // Command input
    document.getElementById('command-input').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') this.handleCommand(e);
    });
  }
  
  async connectToAPI() {
    try {
      console.log('🔌 Connecting to NERV API...');
      const response = await fetch(`${this.apiBaseUrl}/geometry/health`);
      
      if (response.ok) {
        const health = await response.json();
        this.isApiConnected = true;
        this.updateApiStatus('connected', 'success');
        console.log('✅ API connected:', health);
      } else {
        throw new Error('API health check failed');
      }
    } catch (error) {
      console.error('❌ API connection failed:', error);
      this.isApiConnected = false;
      this.updateApiStatus('offline', 'error');
      this.showNotification('API connection failed - using offline mode', 'error');
    }
  }
  
  async loadPlayerCollection() {
    if (!this.isApiConnected) {
      this.updateCollectionDisplay({ collection: { total_elements: 1, elements: { basic_point: { name: 'Basic Point' } } } });
      return;
    }
    
    try {
      const response = await fetch(`${this.apiBaseUrl}/collection/player/default_player`);
      if (response.ok) {
        this.playerCollection = await response.json();
        this.updateCollectionDisplay(this.playerCollection);
        console.log('📊 Collection loaded:', this.playerCollection);
      }
    } catch (error) {
      console.error('❌ Failed to load collection:', error);
    }
  }
  
  selectTool(tool) {
    // Handle special tools
    if (tool === 'clear') {
      this.clearCanvas();
      return;
    }
    
    this.currentTool = tool;
    this.updateToolDisplay();
    this.clearTempObjects();
    
    // Update cursor based on tool
    const canvas = this.stage.container();
    const cursors = {
      point: 'crosshair',
      line: 'crosshair', 
      circle: 'crosshair',
      intersect: 'pointer',
      measure: 'help'
    };
    canvas.style.cursor = cursors[tool] || 'default';
    
    console.log(`🔧 Tool selected: ${tool.toUpperCase()}`);
  }
  
  selectMagi(magi) {
    this.selectedMagi = magi;
    
    // Update UI
    document.querySelectorAll('.magi-tab').forEach(tab => tab.classList.remove('active'));
    document.querySelector(`[data-magi="${magi}"]`).classList.add('active');
    
    // Add system message
    const magiNames = {
      casper: 'CASPER - Construction Assistant',
      melchior: 'MELCHIOR - Mathematical Analyst', 
      balthasar: 'BALTHASAR - Educational Guide'
    };
    
    this.addMagiMessage(magi, `${magiNames[magi]} activated. How can I help with your geometric construction?`);
  }
  
  async handleCanvasClick(e) {
    const pos = this.stage.getPointerPosition();
    const snappedPos = this.snapToGrid(pos);
    
    console.log(`🖱️ Canvas clicked at (${pos.x}, ${pos.y}), snapped to (${snappedPos.x}, ${snappedPos.y}), tool: ${this.currentTool}`);
    
    switch (this.currentTool) {
      case 'point':
        await this.createPoint(snappedPos);
        break;
        
      case 'line':
        await this.handleLineCreation(snappedPos);
        break;
        
      case 'circle':
        await this.handleCircleCreation(snappedPos);
        break;
        
      case 'intersect':
        await this.findIntersectionsAt(snappedPos);
        break;
        
      case 'measure':
        this.measureDistance(snappedPos);
        break;
    }
    
    this.updateObjectCount();
  }
  
  handleCanvasMove(e) {
    if (this.currentTool === 'line' && this.drawingState.isDrawing) {
      this.updateTempLine();
    } else if (this.currentTool === 'circle' && this.drawingState.isDrawing) {
      this.updateTempCircle();
    }
  }
  
  snapToGrid(pos, gridSize = 20) {
    return {
      x: Math.round(pos.x / gridSize) * gridSize,
      y: Math.round(pos.y / gridSize) * gridSize
    };
  }
  
  async createPoint(pos) {
    const pointId = this.generateId('point');
    
    console.log(`🎯 Creating point at (${pos.x}, ${pos.y}) with ID: ${pointId}`);
    console.log(`📍 Layer exists: ${this.layer ? 'Yes' : 'No'}`);
    console.log(`📍 Stage exists: ${this.stage ? 'Yes' : 'No'}`);
    
    try {
      // Create visual point
      const point = new Konva.Circle({
        id: pointId,
        x: pos.x,
        y: pos.y,
        radius: 6,  // Increased radius for visibility
        fill: '#00FFFF',
        stroke: '#FFFFFF',
        strokeWidth: 2,  // Increased stroke width
        draggable: false,
        shadowColor: '#00FFFF',
        shadowBlur: 12,  // Increased shadow
        shadowOpacity: 0.8
      });
      
      console.log(`🔵 Point object created: ${point.id()}`);
      
      // Add label with simplified text
      const labelText = pointId.split('_')[1] ? pointId.split('_')[1].toUpperCase().slice(0, 4) : 'P';
      const label = new Konva.Text({
        x: pos.x + 10,
        y: pos.y - 10,
        text: labelText,
        fontSize: 14,  // Increased font size
        fill: '#FFFFFF',
        fontFamily: 'Arial',  // Changed font for compatibility
        fontStyle: 'bold'
      });
      
      console.log(`🏷️ Label created: ${label.text()}`);
      
      // Add to layer
      this.layer.add(point);
      this.layer.add(label);
      
      console.log(`➕ Added to layer - Points in layer: ${this.layer.children.length}`);
      
      // Force immediate draw
      this.layer.batchDraw();
      
      console.log(`🖼️ Layer draw called - Stage size: ${this.stage.width()}x${this.stage.height()}`);
      
      // Update construction space
      this.constructionSpace.points[pointId] = { x: pos.x, y: pos.y };
      this.constructionSpace.history.push({
        action: 'add_point',
        id: pointId,
        position: pos,
        timestamp: Date.now()
      });
      
      // Show visual feedback
      this.showNotification(`Point created: ${labelText} at (${Math.round(pos.x)}, ${Math.round(pos.y)})`, 'success');
      
      // API call if connected
      console.log(`📡 API connection status: ${this.isApiConnected ? 'Connected' : 'Disconnected'}`);
      if (this.isApiConnected) {
        console.log(`📡 Making API call to create point...`);
        const apiResult = await this.apiCreatePoint(pos.x, pos.y, pointId);
        console.log(`📡 API response:`, apiResult);
      } else {
        console.log('⚠️ Skipping API call - not connected');
      }
      
      console.log(`✅ Point creation completed: ${pointId} at (${pos.x}, ${pos.y})`);
      
      // Update UI counters
      this.updateObjectCount();
      this.updateHistoryDisplay();
      
    } catch (error) {
      console.error('❌ Failed to create point:', error);
      console.error('❌ Error stack:', error.stack);
      this.showNotification('Failed to create point: ' + error.message, 'error');
    }
  }
  
  async handleLineCreation(pos) {
    const nearPoint = this.findNearbyPoint(pos);
    
    if (!this.drawingState.isDrawing) {
      // Start line creation
      if (nearPoint) {
        this.drawingState.isDrawing = true;
        this.drawingState.startPoint = nearPoint;
        console.log(`📏 Line creation started from ${nearPoint.id}`);
      } else {
        this.showNotification('Click on a point to start drawing a line', 'info');
      }
    } else {
      // Complete line creation
      if (nearPoint && nearPoint.id !== this.drawingState.startPoint.id) {
        await this.createLine(this.drawingState.startPoint, nearPoint);
        this.drawingState.isDrawing = false;
        this.drawingState.startPoint = null;
        this.clearTempObjects();
      } else {
        this.showNotification('Click on a different point to complete the line', 'info');
      }
    }
  }
  
  async createLine(point1, point2) {
    const lineId = this.generateId('line');
    
    try {
      const line = new Konva.Line({
        id: lineId,
        points: [point1.pos.x, point1.pos.y, point2.pos.x, point2.pos.y],
        stroke: '#00FF00',
        strokeWidth: 2,
        shadowColor: '#00FF00',
        shadowBlur: 4,
        shadowOpacity: 0.4
      });
      
      this.layer.add(line);
      
      // Update construction space
      this.constructionSpace.lines[lineId] = {
        point1: point1.id,
        point2: point2.id
      };
      this.constructionSpace.history.push({
        action: 'create_line',
        id: lineId,
        points: [point1.id, point2.id],
        timestamp: Date.now()
      });
      
      // API call if connected
      if (this.isApiConnected) {
        await this.apiCreateLine(point1.id, point2.id, lineId);
      }
      
      this.layer.draw();
      console.log(`📏 Line created: ${lineId} between ${point1.id} and ${point2.id}`);
      
      // Check for achievements
      await this.checkForNewElements();
      
    } catch (error) {
      console.error('❌ Failed to create line:', error);
      this.showNotification('Failed to create line', 'error');
    }
  }
  
  async handleCircleCreation(pos) {
    const nearPoint = this.findNearbyPoint(pos);
    
    if (!this.drawingState.isDrawing) {
      // Start circle creation (select center)
      if (nearPoint) {
        this.drawingState.isDrawing = true;
        this.drawingState.startPoint = nearPoint;
        console.log(`⭕ Circle creation started with center ${nearPoint.id}`);
      } else {
        this.showNotification('Click on a point to use as circle center', 'info');
      }
    } else {
      // Complete circle creation (select radius point)
      if (nearPoint && nearPoint.id !== this.drawingState.startPoint.id) {
        await this.createCircle(this.drawingState.startPoint, nearPoint);
        this.drawingState.isDrawing = false;
        this.drawingState.startPoint = null;
        this.clearTempObjects();
      } else {
        this.showNotification('Click on a different point to set the radius', 'info');
      }
    }
  }
  
  async createCircle(centerPoint, radiusPoint) {
    const circleId = this.generateId('circle');
    
    try {
      const radius = Math.sqrt(
        Math.pow(radiusPoint.pos.x - centerPoint.pos.x, 2) + 
        Math.pow(radiusPoint.pos.y - centerPoint.pos.y, 2)
      );
      
      const circle = new Konva.Circle({
        id: circleId,
        x: centerPoint.pos.x,
        y: centerPoint.pos.y,
        radius: radius,
        stroke: '#FF8000',
        strokeWidth: 2,
        fill: 'transparent',
        shadowColor: '#FF8000',
        shadowBlur: 4,
        shadowOpacity: 0.3
      });
      
      this.layer.add(circle);
      
      // Update construction space
      this.constructionSpace.circles[circleId] = {
        center: centerPoint.id,
        radiusPoint: radiusPoint.id,
        radius: radius
      };
      this.constructionSpace.history.push({
        action: 'create_circle',
        id: circleId,
        center: centerPoint.id,
        radiusPoint: radiusPoint.id,
        timestamp: Date.now()
      });
      
      // API call if connected
      if (this.isApiConnected) {
        await this.apiCreateCircle(centerPoint.id, radiusPoint.id, circleId);
      }
      
      this.layer.draw();
      console.log(`⭕ Circle created: ${circleId} with center ${centerPoint.id}`);
      
      // Check for achievements
      await this.checkForNewElements();
      
    } catch (error) {
      console.error('❌ Failed to create circle:', error);
      this.showNotification('Failed to create circle', 'error');
    }
  }
  
  findNearbyPoint(pos) {
    for (const [pointId, point] of Object.entries(this.constructionSpace.points)) {
      const distance = Math.sqrt(
        Math.pow(pos.x - point.x, 2) + Math.pow(pos.y - point.y, 2)
      );
      if (distance <= this.drawingState.snapDistance) {
        return { id: pointId, pos: point };
      }
    }
    return null;
  }
  
  updateTempLine() {
    this.clearTempObjects();
    
    if (this.drawingState.startPoint) {
      const pos = this.stage.getPointerPosition();
      const tempLine = new Konva.Line({
        id: 'temp_line',
        points: [
          this.drawingState.startPoint.pos.x, 
          this.drawingState.startPoint.pos.y, 
          pos.x, 
          pos.y
        ],
        stroke: 'rgba(0, 255, 0, 0.5)',
        strokeWidth: 2,
        dash: [5, 5],
        listening: false
      });
      
      this.layer.add(tempLine);
      this.drawingState.tempObjects.push(tempLine);
      this.layer.draw();
    }
  }
  
  updateTempCircle() {
    this.clearTempObjects();
    
    if (this.drawingState.startPoint) {
      const pos = this.stage.getPointerPosition();
      const radius = Math.sqrt(
        Math.pow(pos.x - this.drawingState.startPoint.pos.x, 2) + 
        Math.pow(pos.y - this.drawingState.startPoint.pos.y, 2)
      );
      
      const tempCircle = new Konva.Circle({
        id: 'temp_circle',
        x: this.drawingState.startPoint.pos.x,
        y: this.drawingState.startPoint.pos.y,
        radius: radius,
        stroke: 'rgba(255, 128, 0, 0.5)',
        strokeWidth: 2,
        dash: [5, 5],
        fill: 'transparent',
        listening: false
      });
      
      this.layer.add(tempCircle);
      this.drawingState.tempObjects.push(tempCircle);
      this.layer.draw();
    }
  }
  
  clearTempObjects() {
    this.drawingState.tempObjects.forEach(obj => obj.destroy());
    this.drawingState.tempObjects = [];
    this.layer.draw();
  }
  
  clearCanvas() {
    // Remove all objects except grid
    this.layer.find('*').forEach(node => {
      if (node.id() !== 'grid') {
        node.destroy();
      }
    });
    
    // Reset construction space
    this.constructionSpace = {
      points: {},
      lines: {},
      circles: {},
      history: []
    };
    
    this.layer.draw();
    this.updateObjectCount();
    this.updateHistoryDisplay();
    
    console.log('🧹 Canvas cleared');
    this.showNotification('Canvas cleared', 'info');
  }
  
  async sendToMagi() {
    const input = document.getElementById('magi-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    this.addMagiMessage('user', message);
    input.value = '';
    
    if (!this.isApiConnected) {
      this.addMagiMessage(this.selectedMagi, 'API connection unavailable. Using offline responses.');
      return;
    }
    
    try {
      const response = await fetch(`${this.apiBaseUrl}/magi/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query_type: 'construction_help',
          content: message,
          construction_space: this.constructionSpace,
          preferred_magi: this.selectedMagi,
          difficulty_level: 'beginner'
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        this.addMagiMessage(result.magi_system, result.content);
        
        if (result.suggestions.length > 0) {
          this.addMagiMessage(result.magi_system, `Suggestions: ${result.suggestions.join('; ')}`);
        }
      } else {
        throw new Error('MAGI query failed');
      }
    } catch (error) {
      console.error('❌ MAGI query failed:', error);
      this.addMagiMessage(this.selectedMagi, 'Sorry, I encountered an error processing your request.');
    }
  }
  
  addMagiMessage(sender, content) {
    const messagesContainer = document.getElementById('magi-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `magi-message ${sender}`;
    
    const timestamp = new Date().toLocaleTimeString();
    messageDiv.innerHTML = `
      <strong>${sender.toUpperCase()}:</strong> ${content}
      <div style="font-size: 0.6rem; opacity: 0.7; margin-top: 2px;">${timestamp}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
  
  async checkForNewElements() {
    if (!this.isApiConnected || !this.playerCollection) return;
    
    try {
      const response = await fetch(`${this.apiBaseUrl}/collection/unlock-element`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_id: 'default_player',
          construction_space: this.constructionSpace,
          completed_construction: this.guessConstructionType()
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.unlocked_elements.length > 0) {
          result.unlocked_elements.forEach(element => {
            this.showNotification(`New element unlocked: ${element.name}!`, 'success');
          });
          await this.loadPlayerCollection(); // Refresh collection display
        }
      }
    } catch (error) {
      console.error('❌ Failed to check for new elements:', error);
    }
  }
  
  guessConstructionType() {
    const lineCount = Object.keys(this.constructionSpace.lines).length;
    const circleCount = Object.keys(this.constructionSpace.circles).length;
    
    if (lineCount >= 3 && circleCount >= 2) return 'equilateral_triangle';
    if (lineCount >= 2 && circleCount >= 2) return 'perpendicular_bisector';
    if (circleCount >= 1) return 'circle';
    if (lineCount >= 1) return 'line_segment';
    return 'basic_construction';
  }
  
  // API helper methods
  async apiCreatePoint(x, y, label) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/geometry/points`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          point_data: { x, y, label },
          construction_space_data: this.constructionSpace
        })
      });
      return response.ok ? await response.json() : null;
    } catch (error) {
      console.error('API point creation failed:', error);
      return null;
    }
  }
  
  async apiCreateLine(point1Id, point2Id, label) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/geometry/lines`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          line_data: { point1_id: point1Id, point2_id: point2Id, label },
          construction_space_data: this.constructionSpace
        })
      });
      return response.ok ? await response.json() : null;
    } catch (error) {
      console.error('API line creation failed:', error);
      return null;
    }
  }
  
  async apiCreateCircle(centerId, radiusPointId, label) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/geometry/circles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          circle_data: { center_id: centerId, radius_point_id: radiusPointId, label },
          construction_space_data: this.constructionSpace
        })
      });
      return response.ok ? await response.json() : null;
    } catch (error) {
      console.error('API circle creation failed:', error);
      return null;
    }
  }
  
  // UI update methods
  updateToolDisplay() {
    document.querySelectorAll('.tool-button').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-tool="${this.currentTool}"]`).classList.add('active');
    document.getElementById('current-tool').textContent = this.currentTool.toUpperCase();
  }
  
  updateObjectCount() {
    const total = Object.keys(this.constructionSpace.points).length + 
                 Object.keys(this.constructionSpace.lines).length + 
                 Object.keys(this.constructionSpace.circles).length;
    document.getElementById('object-count').textContent = total;
    document.getElementById('step-count').textContent = this.constructionSpace.history.length;
  }
  
  updateCollectionDisplay(collection) {
    if (!collection || !collection.collection) return;
    
    const c = collection.collection;
    document.getElementById('total-elements').textContent = c.total_elements || 0;
    document.getElementById('unlocked-elements').textContent = c.unique_elements || 0;
    document.getElementById('player-level').textContent = c.current_level || 1;
    document.getElementById('experience-points').textContent = c.experience_points || 0;
    
    // Update element list
    const listContainer = document.getElementById('element-list');
    listContainer.innerHTML = '';
    
    Object.values(c.elements || {}).forEach(element => {
      const elementDiv = document.createElement('div');
      elementDiv.className = `element-item ${element.rarity || 'common'}`;
      elementDiv.innerHTML = `
        <span>${element.name}</span>
        <span>●</span>
      `;
      listContainer.appendChild(elementDiv);
    });
  }
  
  updateApiStatus(status, type) {
    const dot = document.getElementById('api-dot');
    const text = document.getElementById('api-status');
    const connectionStatus = document.getElementById('api-connection-status');
    const loading = document.getElementById('api-loading');
    
    dot.className = `status-dot ${type}`;
    text.textContent = status === 'connected' ? 'ONLINE' : 'OFFLINE';
    connectionStatus.textContent = status === 'connected' ? 'Connected' : 'Offline';
    loading.style.display = status === 'connected' ? 'none' : 'inline-block';
  }
  
  updateHistoryDisplay() {
    const historyContainer = document.getElementById('history-list');
    historyContainer.innerHTML = '';
    
    if (this.constructionSpace.history.length === 0) {
      historyContainer.innerHTML = '<div style="color: #666; font-style: italic;">No constructions yet...</div>';
      return;
    }
    
    this.constructionSpace.history.slice(-10).reverse().forEach(entry => {
      const historyDiv = document.createElement('div');
      historyDiv.style.cssText = 'margin: 2px 0; padding: 2px; border-left: 2px solid #00FFFF;';
      historyDiv.textContent = `${entry.action.replace('_', ' ')} - ${entry.id}`;
      historyContainer.appendChild(historyDiv);
    });
  }
  
  showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.style.animation = 'slideIn 0.3s ease-out reverse';
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }
  
  startStatusUpdates() {
    setInterval(async () => {
      if (this.isApiConnected) {
        try {
          const response = await fetch(`${this.apiBaseUrl}/geometry/health`);
          if (!response.ok) throw new Error('Health check failed');
        } catch (error) {
          this.isApiConnected = false;
          this.updateApiStatus('offline', 'error');
        }
      } else {
        // Try to reconnect
        await this.connectToAPI();
      }
    }, 30000); // Check every 30 seconds
  }
  
  resizeCanvas() {
    const container = document.getElementById('geometryCanvas');
    const containerRect = container.parentElement.getBoundingClientRect();
    
    this.stage.width(containerRect.width - 2);
    this.stage.height(containerRect.height - 2);
    
    // Redraw grid
    this.layer.findOne('#grid')?.destroy();
    this.addGrid();
    this.layer.draw();
  }
  
  generateId(type) {
    const timestamp = Date.now().toString(36);
    const random = Math.random().toString(36).substr(2, 5);
    return `${type}_${timestamp}_${random}`;
  }
  
  handleCommand(event) {
    const command = event.target.value.trim().toLowerCase();
    if (!command) return;
    
    console.log(`💻 Command: ${command}`);
    
    const commands = {
      'help': () => this.showNotification('Available commands: help, clear, save, load, status', 'info'),
      'clear': () => this.clearCanvas(),
      'status': () => this.showNotification(`API: ${this.isApiConnected ? 'Connected' : 'Offline'}`, 'info'),
      'save': () => this.showNotification('Save functionality coming soon', 'info'),
      'load': () => this.showNotification('Load functionality coming soon', 'info')
    };
    
    if (commands[command]) {
      commands[command]();
    } else {
      this.showNotification(`Unknown command: ${command}`, 'error');
    }
    
    event.target.value = '';
  }
}

// Global functions for HTML event handlers
function sendToMagi() {
  window.nerv.sendToMagi();
}

function handleCommand(event) {
  window.nerv.handleCommand(event);
}

function loadTemplate(templateName) {
  window.nerv.showNotification(`Loading ${templateName} template...`, 'info');
  // Template loading functionality to be implemented
}

function validateConstruction() {
  window.nerv.showNotification('Validating construction...', 'info');
  // Validation functionality to be implemented
}

function saveConstruction() {
  window.nerv.showNotification('Saving construction...', 'info');
  // Save functionality to be implemented
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  try {
    console.log('🚀 Initializing NERV App...');
    
    // Check if required libraries are loaded
    if (typeof Konva === 'undefined') {
      console.error('❌ Konva.js not loaded');
      alert('Required library (Konva.js) failed to load. Please refresh the page.');
      return;
    }
    
    console.log('✅ All dependencies loaded');
    window.nerv = new NERVApp();
    console.log('✅ NERV App initialized successfully');
    
  } catch (error) {
    console.error('❌ Failed to initialize NERV:', error);
    alert('Failed to initialize NERV application. Check console for details.');
  }
});