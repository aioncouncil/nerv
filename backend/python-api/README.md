# NERV Geometry Engine - Python API

FastAPI-based REST API for the NERV geometric construction system.

## Features

- **Geometry Operations**: Points, lines, circles, and intersections
- **Construction Validation**: Step-by-step construction verification  
- **Collection System**: Pokédex-style element collection mechanics
- **MAGI AI Assistants**: AI-powered proof checking and guidance
- **Rust Integration**: High-performance geometric calculations via Rust engine

## Quick Start

```bash
# Install dependencies
pip install -e .

# Start development server
uvicorn app.main:app --reload --port 8001
```

## API Endpoints

- `/api/v1/geometry/` - Basic geometric operations
- `/api/v1/construction/` - Construction validation and execution
- `/api/v1/collection/` - Element collection and progression
- `/api/v1/magi/` - AI assistant services

## Development

This is part of the larger NERV project combining Rust performance with Python flexibility.