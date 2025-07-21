//! Core geometric primitives and operations
//!
//! This module provides the fundamental geometric objects (points, lines, circles)
//! and operations needed for Euclidean construction.

use nalgebra::{Point2, Vector2};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

pub mod primitives;
pub mod operations;
pub mod transformations;

pub use primitives::*;
pub use operations::*;
pub use transformations::*;

/// A point in 2D Euclidean space
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Point {
    pub id: String,
    pub position: Point2<f64>,
    pub label: Option<String>,
    pub is_constructed: bool,
    pub dependencies: Vec<String>,
}

impl Point {
    /// Create a new point
    pub fn new(x: f64, y: f64, label: Option<String>) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            position: Point2::new(x, y),
            label,
            is_constructed: false,
            dependencies: Vec::new(),
        }
    }

    /// Create a constructed point with dependencies
    pub fn constructed(x: f64, y: f64, label: Option<String>, dependencies: Vec<String>) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            position: Point2::new(x, y),
            label,
            is_constructed: true,
            dependencies,
        }
    }

    /// Get the distance to another point
    pub fn distance_to(&self, other: &Point) -> f64 {
        nalgebra::distance(&self.position, &other.position)
    }

    /// Check if this point is approximately equal to another
    pub fn approx_eq(&self, other: &Point, tolerance: f64) -> bool {
        self.distance_to(other) < tolerance
    }
}

/// A line in 2D space
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Line {
    pub id: String,
    pub point1_id: String,
    pub point2_id: String,
    pub label: Option<String>,
    pub dependencies: Vec<String>,
}

impl Line {
    /// Create a new line through two points
    pub fn new(point1_id: String, point2_id: String, label: Option<String>) -> Self {
        let dependencies = vec![point1_id.clone(), point2_id.clone()];
        Self {
            id: Uuid::new_v4().to_string(),
            point1_id,
            point2_id,
            label,
            dependencies,
        }
    }

    /// Get the direction vector of this line
    pub fn direction(&self, point1: &Point, point2: &Point) -> Vector2<f64> {
        point2.position - point1.position
    }

    /// Check if a point lies on this line
    pub fn contains_point(&self, point: &Point, p1: &Point, p2: &Point, tolerance: f64) -> bool {
        let cross_product = (point.position.y - p1.position.y) * (p2.position.x - p1.position.x) 
                          - (point.position.x - p1.position.x) * (p2.position.y - p1.position.y);
        cross_product.abs() < tolerance
    }
}

/// A circle in 2D space
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Circle {
    pub id: String,
    pub center_id: String,
    pub radius_point_id: String,
    pub label: Option<String>,
    pub dependencies: Vec<String>,
}

impl Circle {
    /// Create a new circle with center and radius point
    pub fn new(center_id: String, radius_point_id: String, label: Option<String>) -> Self {
        let dependencies = vec![center_id.clone(), radius_point_id.clone()];
        Self {
            id: Uuid::new_v4().to_string(),
            center_id,
            radius_point_id,
            label,
            dependencies,
        }
    }

    /// Calculate the radius of this circle
    pub fn radius(&self, center: &Point, radius_point: &Point) -> f64 {
        center.distance_to(radius_point)
    }

    /// Check if a point lies on this circle
    pub fn contains_point(&self, point: &Point, center: &Point, radius_point: &Point, tolerance: f64) -> bool {
        let radius = self.radius(center, radius_point);
        let distance = center.distance_to(point);
        (distance - radius).abs() < tolerance
    }
}

/// Represents any geometric object in the construction
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum GeometricObject {
    Point(Point),
    Line(Line),
    Circle(Circle),
}

impl GeometricObject {
    /// Get the ID of this geometric object
    pub fn id(&self) -> &str {
        match self {
            GeometricObject::Point(p) => &p.id,
            GeometricObject::Line(l) => &l.id,
            GeometricObject::Circle(c) => &c.id,
        }
    }

    /// Get the dependencies of this geometric object
    pub fn dependencies(&self) -> &[String] {
        match self {
            GeometricObject::Point(p) => &p.dependencies,
            GeometricObject::Line(l) => &l.dependencies,
            GeometricObject::Circle(c) => &c.dependencies,
        }
    }

    /// Get the label of this geometric object
    pub fn label(&self) -> Option<&str> {
        match self {
            GeometricObject::Point(p) => p.label.as_deref(),
            GeometricObject::Line(l) => l.label.as_deref(),
            GeometricObject::Circle(c) => c.label.as_deref(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_abs_diff_eq;

    #[test]
    fn test_point_creation() {
        let point = Point::new(1.0, 2.0, Some("A".to_string()));
        assert_eq!(point.position.x, 1.0);
        assert_eq!(point.position.y, 2.0);
        assert_eq!(point.label, Some("A".to_string()));
        assert!(!point.is_constructed);
    }

    #[test]
    fn test_point_distance() {
        let p1 = Point::new(0.0, 0.0, None);
        let p2 = Point::new(3.0, 4.0, None);
        assert_abs_diff_eq!(p1.distance_to(&p2), 5.0, epsilon = 1e-10);
    }

    #[test]
    fn test_line_creation() {
        let line = Line::new("p1".to_string(), "p2".to_string(), Some("AB".to_string()));
        assert_eq!(line.point1_id, "p1");
        assert_eq!(line.point2_id, "p2");
        assert_eq!(line.label, Some("AB".to_string()));
        assert_eq!(line.dependencies, vec!["p1", "p2"]);
    }

    #[test]
    fn test_circle_creation() {
        let circle = Circle::new("center".to_string(), "radius_point".to_string(), Some("O".to_string()));
        assert_eq!(circle.center_id, "center");
        assert_eq!(circle.radius_point_id, "radius_point");
        assert_eq!(circle.label, Some("O".to_string()));
        assert_eq!(circle.dependencies, vec!["center", "radius_point"]);
    }
}