//! Construction management and validation system

use crate::geometry::{GeometricObject, Point, Line, Circle};
use crate::{GeometryError, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use uuid::Uuid;

/// A construction space containing all geometric objects and their relationships
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConstructionSpace {
    /// All points in the construction
    pub points: HashMap<String, Point>,
    /// All lines in the construction
    pub lines: HashMap<String, Line>,
    /// All circles in the construction
    pub circles: HashMap<String, Circle>,
    /// Construction history for playback
    pub history: Vec<ConstructionStep>,
}

impl ConstructionSpace {
    /// Create a new empty construction space
    pub fn new() -> Self {
        Self {
            points: HashMap::new(),
            lines: HashMap::new(),
            circles: HashMap::new(),
            history: Vec::new(),
        }
    }

    /// Add a point to the construction space
    pub fn add_point(&mut self, point: Point) -> String {
        let id = point.id.clone();
        let step = ConstructionStep::AddPoint { point: point.clone() };
        self.history.push(step);
        self.points.insert(id.clone(), point);
        id
    }

    /// Construct a line through two points
    pub fn construct_line(&mut self, point1_id: &str, point2_id: &str, label: Option<String>) -> Result<String> {
        // Validate that points exist
        if !self.points.contains_key(point1_id) {
            return Err(GeometryError::PointNotFound { 
                id: point1_id.to_string() 
            });
        }
        if !self.points.contains_key(point2_id) {
            return Err(GeometryError::PointNotFound { 
                id: point2_id.to_string() 
            });
        }

        // Check that points are not the same
        if point1_id == point2_id {
            return Err(GeometryError::InvalidConstruction { 
                reason: "Cannot create line with identical points".to_string() 
            });
        }

        let line = Line::new(point1_id.to_string(), point2_id.to_string(), label);
        let id = line.id.clone();
        
        let step = ConstructionStep::ConstructLine { 
            line: line.clone(),
            point1_id: point1_id.to_string(),
            point2_id: point2_id.to_string(),
        };
        self.history.push(step);
        self.lines.insert(id.clone(), line);
        
        Ok(id)
    }

    /// Construct a circle with center and radius point
    pub fn construct_circle(&mut self, center_id: &str, radius_point_id: &str, label: Option<String>) -> Result<String> {
        // Validate that points exist
        if !self.points.contains_key(center_id) {
            return Err(GeometryError::PointNotFound { 
                id: center_id.to_string() 
            });
        }
        if !self.points.contains_key(radius_point_id) {
            return Err(GeometryError::PointNotFound { 
                id: radius_point_id.to_string() 
            });
        }

        // Check that points are not the same
        if center_id == radius_point_id {
            return Err(GeometryError::InvalidConstruction { 
                reason: "Center and radius point cannot be the same".to_string() 
            });
        }

        let circle = Circle::new(center_id.to_string(), radius_point_id.to_string(), label);
        let id = circle.id.clone();
        
        let step = ConstructionStep::ConstructCircle { 
            circle: circle.clone(),
            center_id: center_id.to_string(),
            radius_point_id: radius_point_id.to_string(),
        };
        self.history.push(step);
        self.circles.insert(id.clone(), circle);
        
        Ok(id)
    }

    /// Find intersections between two geometric objects
    pub fn find_intersections(&mut self, obj1_id: &str, obj2_id: &str) -> Result<Vec<Point>> {
        use crate::geometry::operations::{line_line_intersection, line_circle_intersection, circle_circle_intersection};

        // Determine object types and get intersections
        let intersections = if let (Some(line1), Some(line2)) = (self.lines.get(obj1_id), self.lines.get(obj2_id)) {
            // Line-Line intersection
            let p1a = self.points.get(&line1.point1_id).unwrap();
            let p1b = self.points.get(&line1.point2_id).unwrap();
            let p2a = self.points.get(&line2.point1_id).unwrap();
            let p2b = self.points.get(&line2.point2_id).unwrap();
            line_line_intersection(line1, p1a, p1b, line2, p2a, p2b)?
        } else if let (Some(line), Some(circle)) = (self.lines.get(obj1_id), self.circles.get(obj2_id)) {
            // Line-Circle intersection
            let p1 = self.points.get(&line.point1_id).unwrap();
            let p2 = self.points.get(&line.point2_id).unwrap();
            let center = self.points.get(&circle.center_id).unwrap();
            let radius_point = self.points.get(&circle.radius_point_id).unwrap();
            line_circle_intersection(line, p1, p2, circle, center, radius_point)?
        } else if let (Some(circle), Some(line)) = (self.circles.get(obj1_id), self.lines.get(obj2_id)) {
            // Circle-Line intersection (swap order)
            let p1 = self.points.get(&line.point1_id).unwrap();
            let p2 = self.points.get(&line.point2_id).unwrap();
            let center = self.points.get(&circle.center_id).unwrap();
            let radius_point = self.points.get(&circle.radius_point_id).unwrap();
            line_circle_intersection(line, p1, p2, circle, center, radius_point)?
        } else if let (Some(circle1), Some(circle2)) = (self.circles.get(obj1_id), self.circles.get(obj2_id)) {
            // Circle-Circle intersection
            let center1 = self.points.get(&circle1.center_id).unwrap();
            let radius_point1 = self.points.get(&circle1.radius_point_id).unwrap();
            let center2 = self.points.get(&circle2.center_id).unwrap();
            let radius_point2 = self.points.get(&circle2.radius_point_id).unwrap();
            circle_circle_intersection(circle1, center1, radius_point1, circle2, center2, radius_point2)?
        } else {
            return Err(GeometryError::InvalidConstruction { 
                reason: "Invalid object IDs for intersection".to_string() 
            });
        };

        // Add intersection points to the construction space
        let mut point_ids = Vec::new();
        for point in intersections {
            let id = self.add_point(point);
            point_ids.push(id);
        }

        // Get the points to return
        let result_points: Vec<Point> = point_ids.iter()
            .map(|id| self.points.get(id).unwrap().clone())
            .collect();

        Ok(result_points)
    }

    /// Validate a construction step
    pub fn validate_step(&self, step: &ConstructionStep) -> bool {
        match step {
            ConstructionStep::AddPoint { .. } => true, // Always valid
            ConstructionStep::ConstructLine { point1_id, point2_id, .. } => {
                self.points.contains_key(point1_id) && 
                self.points.contains_key(point2_id) &&
                point1_id != point2_id
            }
            ConstructionStep::ConstructCircle { center_id, radius_point_id, .. } => {
                self.points.contains_key(center_id) && 
                self.points.contains_key(radius_point_id) &&
                center_id != radius_point_id
            }
            ConstructionStep::FindIntersections { obj1_id, obj2_id } => {
                (self.lines.contains_key(obj1_id) || self.circles.contains_key(obj1_id)) &&
                (self.lines.contains_key(obj2_id) || self.circles.contains_key(obj2_id))
            }
        }
    }

    /// Get all objects in the construction space
    pub fn get_all_objects(&self) -> Vec<GeometricObject> {
        let mut objects = Vec::new();
        
        for point in self.points.values() {
            objects.push(GeometricObject::Point(point.clone()));
        }
        
        for line in self.lines.values() {
            objects.push(GeometricObject::Line(line.clone()));
        }
        
        for circle in self.circles.values() {
            objects.push(GeometricObject::Circle(circle.clone()));
        }
        
        objects
    }

    /// Clear all constructions
    pub fn clear(&mut self) {
        self.points.clear();
        self.lines.clear();
        self.circles.clear();
        self.history.clear();
    }

    /// Get the number of objects in the construction
    pub fn object_count(&self) -> usize {
        self.points.len() + self.lines.len() + self.circles.len()
    }
}

/// Represents a single construction step that can be replayed
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ConstructionStep {
    AddPoint { 
        point: Point 
    },
    ConstructLine { 
        line: Line,
        point1_id: String,
        point2_id: String,
    },
    ConstructCircle { 
        circle: Circle,
        center_id: String,
        radius_point_id: String,
    },
    FindIntersections { 
        obj1_id: String,
        obj2_id: String,
    },
}

impl ConstructionStep {
    /// Get the type of construction step as a string
    pub fn step_type(&self) -> &'static str {
        match self {
            ConstructionStep::AddPoint { .. } => "add_point",
            ConstructionStep::ConstructLine { .. } => "construct_line",
            ConstructionStep::ConstructCircle { .. } => "construct_circle",
            ConstructionStep::FindIntersections { .. } => "find_intersections",
        }
    }

    /// Get dependencies for this step
    pub fn dependencies(&self) -> Vec<String> {
        match self {
            ConstructionStep::AddPoint { .. } => Vec::new(),
            ConstructionStep::ConstructLine { point1_id, point2_id, .. } => {
                vec![point1_id.clone(), point2_id.clone()]
            }
            ConstructionStep::ConstructCircle { center_id, radius_point_id, .. } => {
                vec![center_id.clone(), radius_point_id.clone()]
            }
            ConstructionStep::FindIntersections { obj1_id, obj2_id } => {
                vec![obj1_id.clone(), obj2_id.clone()]
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_construction_space_new() {
        let space = ConstructionSpace::new();
        assert_eq!(space.points.len(), 0);
        assert_eq!(space.lines.len(), 0);
        assert_eq!(space.circles.len(), 0);
        assert_eq!(space.history.len(), 0);
    }

    #[test]
    fn test_add_point() {
        let mut space = ConstructionSpace::new();
        let point = Point::new(1.0, 2.0, Some("A".to_string()));
        let id = space.add_point(point.clone());
        
        assert_eq!(space.points.len(), 1);
        assert_eq!(space.history.len(), 1);
        assert!(space.points.contains_key(&id));
    }

    #[test]
    fn test_construct_line() {
        let mut space = ConstructionSpace::new();
        
        let point1 = Point::new(0.0, 0.0, Some("A".to_string()));
        let point2 = Point::new(1.0, 1.0, Some("B".to_string()));
        let id1 = space.add_point(point1);
        let id2 = space.add_point(point2);
        
        let line_id = space.construct_line(&id1, &id2, Some("AB".to_string())).unwrap();
        
        assert_eq!(space.lines.len(), 1);
        assert!(space.lines.contains_key(&line_id));
        assert_eq!(space.history.len(), 3); // 2 points + 1 line
    }

    #[test]
    fn test_construct_line_invalid_points() {
        let mut space = ConstructionSpace::new();
        
        let result = space.construct_line("invalid1", "invalid2", None);
        assert!(result.is_err());
    }

    #[test]
    fn test_construct_circle() {
        let mut space = ConstructionSpace::new();
        
        let center = Point::new(0.0, 0.0, Some("O".to_string()));
        let radius_point = Point::new(1.0, 0.0, Some("A".to_string()));
        let center_id = space.add_point(center);
        let radius_id = space.add_point(radius_point);
        
        let circle_id = space.construct_circle(&center_id, &radius_id, Some("Circle".to_string())).unwrap();
        
        assert_eq!(space.circles.len(), 1);
        assert!(space.circles.contains_key(&circle_id));
        assert_eq!(space.history.len(), 3); // 2 points + 1 circle
    }

    #[test]
    fn test_line_line_intersection() {
        let mut space = ConstructionSpace::new();
        
        // Create two intersecting lines
        let p1 = space.add_point(Point::new(0.0, 0.0, None));
        let p2 = space.add_point(Point::new(2.0, 0.0, None));
        let p3 = space.add_point(Point::new(1.0, -1.0, None));
        let p4 = space.add_point(Point::new(1.0, 1.0, None));
        
        let line1 = space.construct_line(&p1, &p2, None).unwrap();
        let line2 = space.construct_line(&p3, &p4, None).unwrap();
        
        let intersections = space.find_intersections(&line1, &line2).unwrap();
        
        assert_eq!(intersections.len(), 1);
        assert!((intersections[0].position.x - 1.0).abs() < 1e-10);
        assert!((intersections[0].position.y - 0.0).abs() < 1e-10);
    }

    #[test]
    fn test_validate_step() {
        let mut space = ConstructionSpace::new();
        let point1 = Point::new(0.0, 0.0, None);
        let point2 = Point::new(1.0, 1.0, None);
        let id1 = space.add_point(point1.clone());
        let id2 = space.add_point(point2.clone());
        
        let line = Line::new(id1.clone(), id2.clone(), None);
        let valid_step = ConstructionStep::ConstructLine {
            line: line.clone(),
            point1_id: id1.clone(),
            point2_id: id2.clone(),
        };
        
        let invalid_step = ConstructionStep::ConstructLine {
            line,
            point1_id: "invalid".to_string(),
            point2_id: id2,
        };
        
        assert!(space.validate_step(&valid_step));
        assert!(!space.validate_step(&invalid_step));
    }
}