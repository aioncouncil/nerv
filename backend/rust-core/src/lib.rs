//! NERV Geometry Engine - Simplified for initial testing

use wasm_bindgen::prelude::*;

pub mod geometry;
pub mod construction; 
pub mod collection;
pub mod utils;

#[wasm_bindgen]
extern "C" {
    #[wasm_bindgen(js_namespace = console)]
    fn log(s: &str);
}

macro_rules! console_log {
    ($($t:tt)*) => (log(&format_args!($($t)*).to_string()))
}

/// Initialize the WASM module
#[wasm_bindgen(start)]
pub fn main() {
    console_log!("NERV Geometry Engine initialized");
}

/// Core geometric engine for WebAssembly
#[wasm_bindgen]
pub struct GeometryEngine {
    construction_space: construction::ConstructionSpace,
}

#[wasm_bindgen]
impl GeometryEngine {
    /// Create a new geometry engine
    #[wasm_bindgen(constructor)]
    pub fn new() -> Self {
        Self {
            construction_space: construction::ConstructionSpace::new(),
        }
    }

    /// Add a point to the construction space
    #[wasm_bindgen]
    pub fn add_point(&mut self, x: f64, y: f64, label: Option<String>) -> String {
        let point = geometry::Point::new(x, y, label);
        self.construction_space.add_point(point)
    }

    /// Construct a line through two points
    #[wasm_bindgen]
    pub fn construct_line(&mut self, point1_id: &str, point2_id: &str, label: Option<String>) -> std::result::Result<String, String> {
        self.construction_space
            .construct_line(point1_id, point2_id, label)
            .map_err(|e| e.to_string())
    }

    /// Construct a circle with center and radius point
    #[wasm_bindgen]
    pub fn construct_circle(&mut self, center_id: &str, radius_point_id: &str, label: Option<String>) -> std::result::Result<String, String> {
        self.construction_space
            .construct_circle(center_id, radius_point_id, label)
            .map_err(|e| e.to_string())
    }

    /// Get construction space info as JSON string
    #[wasm_bindgen]
    pub fn get_info(&self) -> String {
        format!("Points: {}, Lines: {}, Circles: {}", 
                self.construction_space.points.len(),
                self.construction_space.lines.len(), 
                self.construction_space.circles.len())
    }
}

/// Error types for the geometry engine
#[derive(Debug, thiserror::Error)]
pub enum GeometryError {
    #[error("Point not found: {id}")]
    PointNotFound { id: String },
    
    #[error("Invalid construction: {reason}")]
    InvalidConstruction { reason: String },
    
    #[error("No intersections found")]
    NoIntersections,
    
    #[error("Graph error: {0}")]
    GraphError(String),
}

pub type Result<T> = std::result::Result<T, GeometryError>;