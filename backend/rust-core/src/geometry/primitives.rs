//! Basic geometric primitives and their properties

use nalgebra::{Point2, Vector2};
use serde::{Deserialize, Serialize};

/// Tolerance for floating point comparisons
pub const EPSILON: f64 = 1e-10;

/// A ray starting from a point in a direction
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Ray {
    pub origin: Point2<f64>,
    pub direction: Vector2<f64>,
}

impl Ray {
    /// Create a new ray
    pub fn new(origin: Point2<f64>, direction: Vector2<f64>) -> Self {
        Self {
            origin,
            direction: direction.normalize(),
        }
    }

    /// Get a point on the ray at parameter t
    pub fn point_at(&self, t: f64) -> Point2<f64> {
        self.origin + t * self.direction
    }
}

/// A line segment between two points
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Segment {
    pub start: Point2<f64>,
    pub end: Point2<f64>,
}

impl Segment {
    /// Create a new segment
    pub fn new(start: Point2<f64>, end: Point2<f64>) -> Self {
        Self { start, end }
    }

    /// Get the length of the segment
    pub fn length(&self) -> f64 {
        nalgebra::distance(&self.start, &self.end)
    }

    /// Get the midpoint of the segment
    pub fn midpoint(&self) -> Point2<f64> {
        Point2::new(
            (self.start.x + self.end.x) / 2.0,
            (self.start.y + self.end.y) / 2.0,
        )
    }

    /// Get the direction vector of the segment
    pub fn direction(&self) -> Vector2<f64> {
        (self.end - self.start).normalize()
    }

    /// Check if a point lies on this segment
    pub fn contains_point(&self, point: &Point2<f64>, tolerance: f64) -> bool {
        // Check if point is collinear with segment
        let cross_product = (point.y - self.start.y) * (self.end.x - self.start.x)
                          - (point.x - self.start.x) * (self.end.y - self.start.y);
        
        if cross_product.abs() > tolerance {
            return false;
        }

        // Check if point is within segment bounds
        let dot_product = (point.x - self.start.x) * (self.end.x - self.start.x)
                        + (point.y - self.start.y) * (self.end.y - self.start.y);
        
        let squared_length = (self.end.x - self.start.x).powi(2) + (self.end.y - self.start.y).powi(2);
        
        dot_product >= -tolerance && dot_product <= squared_length + tolerance
    }
}

/// An arc on a circle
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Arc {
    pub center: Point2<f64>,
    pub radius: f64,
    pub start_angle: f64,
    pub end_angle: f64,
}

impl Arc {
    /// Create a new arc
    pub fn new(center: Point2<f64>, radius: f64, start_angle: f64, end_angle: f64) -> Self {
        Self {
            center,
            radius,
            start_angle,
            end_angle,
        }
    }

    /// Get a point on the arc at the given angle
    pub fn point_at_angle(&self, angle: f64) -> Point2<f64> {
        Point2::new(
            self.center.x + self.radius * angle.cos(),
            self.center.y + self.radius * angle.sin(),
        )
    }

    /// Check if an angle is within this arc
    pub fn contains_angle(&self, angle: f64) -> bool {
        let normalized_start = self.start_angle % (2.0 * std::f64::consts::PI);
        let normalized_end = self.end_angle % (2.0 * std::f64::consts::PI);
        let normalized_angle = angle % (2.0 * std::f64::consts::PI);

        if normalized_start <= normalized_end {
            normalized_angle >= normalized_start && normalized_angle <= normalized_end
        } else {
            normalized_angle >= normalized_start || normalized_angle <= normalized_end
        }
    }

    /// Get the arc length
    pub fn length(&self) -> f64 {
        let angle_diff = (self.end_angle - self.start_angle).abs();
        self.radius * angle_diff
    }
}

/// A polygon defined by vertices
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Polygon {
    pub vertices: Vec<Point2<f64>>,
}

impl Polygon {
    /// Create a new polygon
    pub fn new(vertices: Vec<Point2<f64>>) -> Self {
        Self { vertices }
    }

    /// Check if the polygon is convex
    pub fn is_convex(&self) -> bool {
        if self.vertices.len() < 3 {
            return false;
        }

        let mut sign = None;
        let n = self.vertices.len();

        for i in 0..n {
            let p1 = &self.vertices[i];
            let p2 = &self.vertices[(i + 1) % n];
            let p3 = &self.vertices[(i + 2) % n];

            let cross_product = (p2.x - p1.x) * (p3.y - p2.y) - (p2.y - p1.y) * (p3.x - p2.x);

            if cross_product.abs() > EPSILON {
                let current_sign = cross_product > 0.0;
                if let Some(prev_sign) = sign {
                    if current_sign != prev_sign {
                        return false;
                    }
                } else {
                    sign = Some(current_sign);
                }
            }
        }

        true
    }

    /// Calculate the area of the polygon
    pub fn area(&self) -> f64 {
        if self.vertices.len() < 3 {
            return 0.0;
        }

        let mut area = 0.0;
        let n = self.vertices.len();

        for i in 0..n {
            let j = (i + 1) % n;
            area += self.vertices[i].x * self.vertices[j].y;
            area -= self.vertices[j].x * self.vertices[i].y;
        }

        area.abs() / 2.0
    }

    /// Calculate the centroid of the polygon
    pub fn centroid(&self) -> Point2<f64> {
        let mut centroid = Point2::new(0.0, 0.0);
        let mut area = 0.0;
        let n = self.vertices.len();

        for i in 0..n {
            let j = (i + 1) % n;
            let cross = self.vertices[i].x * self.vertices[j].y - self.vertices[j].x * self.vertices[i].y;
            area += cross;
            centroid.x += (self.vertices[i].x + self.vertices[j].x) * cross;
            centroid.y += (self.vertices[i].y + self.vertices[j].y) * cross;
        }

        area /= 2.0;
        if area.abs() > EPSILON {
            centroid.x /= 6.0 * area;
            centroid.y /= 6.0 * area;
        }

        centroid
    }
}

/// Triangle with additional geometric properties
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Triangle {
    pub a: Point2<f64>,
    pub b: Point2<f64>,
    pub c: Point2<f64>,
}

impl Triangle {
    /// Create a new triangle
    pub fn new(a: Point2<f64>, b: Point2<f64>, c: Point2<f64>) -> Self {
        Self { a, b, c }
    }

    /// Calculate the area using the cross product
    pub fn area(&self) -> f64 {
        let ab = self.b - self.a;
        let ac = self.c - self.a;
        0.5 * (ab.x * ac.y - ab.y * ac.x).abs()
    }

    /// Calculate the perimeter
    pub fn perimeter(&self) -> f64 {
        nalgebra::distance(&self.a, &self.b) + 
        nalgebra::distance(&self.b, &self.c) + 
        nalgebra::distance(&self.c, &self.a)
    }

    /// Calculate the circumradius
    pub fn circumradius(&self) -> f64 {
        let a = nalgebra::distance(&self.b, &self.c);
        let b = nalgebra::distance(&self.c, &self.a);
        let c = nalgebra::distance(&self.a, &self.b);
        
        let area = self.area();
        if area < EPSILON {
            return f64::INFINITY;
        }
        
        (a * b * c) / (4.0 * area)
    }

    /// Calculate the inradius
    pub fn inradius(&self) -> f64 {
        let area = self.area();
        let perimeter = self.perimeter();
        
        if perimeter < EPSILON {
            return 0.0;
        }
        
        area / (perimeter / 2.0)
    }

    /// Check if the triangle is right-angled
    pub fn is_right_angled(&self, tolerance: f64) -> bool {
        let a = nalgebra::distance(&self.b, &self.c);
        let b = nalgebra::distance(&self.c, &self.a);
        let c = nalgebra::distance(&self.a, &self.b);

        let sides = [a, b, c];
        for i in 0..3 {
            let hypotenuse = sides[i];
            let leg1 = sides[(i + 1) % 3];
            let leg2 = sides[(i + 2) % 3];
            
            if (hypotenuse * hypotenuse - leg1 * leg1 - leg2 * leg2).abs() < tolerance {
                return true;
            }
        }
        
        false
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_abs_diff_eq;

    #[test]
    fn test_segment_length() {
        let seg = Segment::new(Point2::new(0.0, 0.0), Point2::new(3.0, 4.0));
        assert_abs_diff_eq!(seg.length(), 5.0, epsilon = EPSILON);
    }

    #[test]
    fn test_segment_midpoint() {
        let seg = Segment::new(Point2::new(1.0, 2.0), Point2::new(3.0, 6.0));
        let midpoint = seg.midpoint();
        assert_abs_diff_eq!(midpoint.x, 2.0, epsilon = EPSILON);
        assert_abs_diff_eq!(midpoint.y, 4.0, epsilon = EPSILON);
    }

    #[test]
    fn test_triangle_area() {
        let triangle = Triangle::new(
            Point2::new(0.0, 0.0),
            Point2::new(4.0, 0.0),
            Point2::new(0.0, 3.0),
        );
        assert_abs_diff_eq!(triangle.area(), 6.0, epsilon = EPSILON);
    }

    #[test]
    fn test_triangle_is_right_angled() {
        let right_triangle = Triangle::new(
            Point2::new(0.0, 0.0),
            Point2::new(3.0, 0.0),
            Point2::new(0.0, 4.0),
        );
        assert!(right_triangle.is_right_angled(EPSILON));

        let non_right_triangle = Triangle::new(
            Point2::new(0.0, 0.0),
            Point2::new(2.0, 0.0),
            Point2::new(1.0, 2.0),
        );
        assert!(!non_right_triangle.is_right_angled(EPSILON));
    }

    #[test]
    fn test_polygon_area() {
        // Square with side length 2
        let square = Polygon::new(vec![
            Point2::new(0.0, 0.0),
            Point2::new(2.0, 0.0),
            Point2::new(2.0, 2.0),
            Point2::new(0.0, 2.0),
        ]);
        assert_abs_diff_eq!(square.area(), 4.0, epsilon = EPSILON);
    }

    #[test]
    fn test_polygon_is_convex() {
        let square = Polygon::new(vec![
            Point2::new(0.0, 0.0),
            Point2::new(1.0, 0.0),
            Point2::new(1.0, 1.0),
            Point2::new(0.0, 1.0),
        ]);
        assert!(square.is_convex());

        // L-shaped polygon (concave)
        let l_shape = Polygon::new(vec![
            Point2::new(0.0, 0.0),
            Point2::new(2.0, 0.0),
            Point2::new(2.0, 1.0),
            Point2::new(1.0, 1.0),
            Point2::new(1.0, 2.0),
            Point2::new(0.0, 2.0),
        ]);
        assert!(!l_shape.is_convex());
    }
}