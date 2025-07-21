# NERV: Euclidean Geometry Pokédex System

A gamified interactive geometric construction system that combines the precision of Euclidean geometry with the engaging mechanics of a Pokédex collection game.

## 🎯 Overview

NERV (Neural Euclidean Reality Visualization) is an industrial-grade system for learning, constructing, and proving geometric theorems through interactive gameplay. Users "catch" geometric elements (points, lines, circles) and use them to construct complex propositions, building a collection of geometric knowledge.

## 🏗️ Architecture

```
nerv/
├── backend/                    # Backend services
│   ├── rust-core/             # High-performance geometric engine
│   ├── python-api/            # FastAPI backend with AI integration
│   ├── shared-types/          # Shared data structures
│   └── database/              # Neo4j graph database setup
├── frontend/                   # React + TypeScript frontend
│   ├── src/                   # Source code
│   ├── components/            # Reusable UI components
│   └── assets/                # Static assets
├── shared/                     # Shared utilities and types
├── tests/                      # Comprehensive test suite
├── docs/                       # Documentation
└── deployment/                 # Docker and deployment configs
```

## 🚀 Key Features

### Core Gameplay
- **Element Collection**: Catch geometric elements like Pokémon
- **Construction System**: Use collected elements to build complex propositions
- **Proof Recording**: Record and playback construction sequences
- **Progressive Difficulty**: Unlock advanced elements through mastery

### Technical Features
- **High-Performance Rust Core**: WebAssembly-powered geometric calculations
- **AI Assistants (MAGI)**: Proof checking and construction guidance
- **Graph Database**: Neo4j for storing geometric relationships
- **Real-time Collaboration**: Shared construction spaces
- **Obsidian-like Notes**: Integrated knowledge management

## 🛠️ Tech Stack

### Backend
- **Rust**: Core geometric engine, graph operations, WebAssembly
- **Python**: AI/ML integration, FastAPI, data analysis
- **Neo4j**: Graph database for geometric relationships
- **PostgreSQL**: User data and session management

### Frontend
- **React + TypeScript**: Modern web framework
- **Konva.js**: Interactive canvas for geometric construction
- **Three.js**: 3D visualization and NERV interface
- **WebAssembly**: High-performance client-side calculations

### Infrastructure
- **Docker**: Containerized deployment
- **GitHub Actions**: CI/CD pipeline
- **PyO3**: Rust-Python integration
- **gRPC**: Inter-service communication

## 🎮 Game Mechanics

### Collection System
1. **Points**: Basic elements - caught through coordinate placement
2. **Lines**: Constructed using two points - unlock linear propositions
3. **Circles**: Constructed using center + radius - unlock circular geometry
4. **Propositions**: Complex theorems built from simpler elements

### Progression System
- **Euclidean Levels**: Progress through increasingly complex geometry
- **Proposition Pokédex**: Complete catalog of geometric theorems
- **Achievement System**: Rewards for elegant constructions
- **Mastery Tracking**: Competency in different geometric domains

## 🤖 AI Integration (MAGI System)

### Three AI Assistants
- **MELCHIOR**: Construction guidance and hints
- **BALTHASAR**: Proof verification and logic checking  
- **CASPER**: Pattern recognition and advanced insights

## 📊 Development Phases

### Phase 1: Core Foundation
- [x] Project structure setup
- [ ] Rust geometric engine
- [ ] Basic web interface
- [ ] Graph database integration

### Phase 2: Interactive Canvas
- [ ] Geometric construction tools
- [ ] Element collection mechanics
- [ ] Basic AI integration

### Phase 3: Advanced Features
- [ ] Proof recording system
- [ ] Collaboration features
- [ ] Advanced gamification

### Phase 4: Production Ready
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Deployment automation

## 🧪 Development

```bash
# Setup development environment
npm install
cargo build
pip install -r requirements.txt

# Run development servers
docker-compose up -d    # Database services
npm run dev            # Frontend
cargo run             # Rust backend
python -m uvicorn main:app --reload  # Python API
```

## 🤝 Contributing

This project follows industrial-grade development practices:
- Comprehensive testing (>80% coverage)
- Code reviews for all changes
- Automated CI/CD pipeline
- Clear documentation requirements

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details

---

*"Understanding geometry through play, mastering proofs through practice."*