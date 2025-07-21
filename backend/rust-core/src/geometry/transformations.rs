//! Geometric transformations and symmetry operations

use nalgebra::{Matrix3, Point2, Vector2};
use serde::{Deserialize, Serialize};

/// A 2D transformation matrix
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Transform2D {
    pub matrix: Matrix3<f64>,
}

impl Transform2D {
    /// Create an identity transformation
    pub fn identity() -> Self {
        Self {
            matrix: Matrix3::identity(),
        }
    }

    /// Create a translation transformation
    pub fn translation(dx: f64, dy: f64) -> Self {
        let mut matrix = Matrix3::identity();
        matrix[(0, 2)] = dx;
        matrix[(1, 2)] = dy;
        Self { matrix }
    }

    /// Create a rotation transformation around the origin
    pub fn rotation(angle: f64) -> Self {
        let cos_a = angle.cos();
        let sin_a = angle.sin();
        
        let matrix = Matrix3::new(
            cos_a, -sin_a, 0.0,
            sin_a, cos_a, 0.0,
            0.0, 0.0, 1.0,
        );
        
        Self { matrix }
    }

    /// Create a rotation transformation around a point
    pub fn rotation_around_point(angle: f64, center: Point2<f64>) -> Self {
        let translate_to_origin = Self::translation(-center.x, -center.y);
        let rotate = Self::rotation(angle);
        let translate_back = Self::translation(center.x, center.y);
        
        translate_back.compose(&rotate).compose(&translate_to_origin)
    }

    /// Create a scaling transformation
    pub fn scaling(sx: f64, sy: f64) -> Self {
        let matrix = Matrix3::new(
            sx, 0.0, 0.0,
            0.0, sy, 0.0,
            0.0, 0.0, 1.0,
        );
        
        Self { matrix }
    }

    /// Create a uniform scaling transformation
    pub fn uniform_scaling(scale: f64) -> Self {
        Self::scaling(scale, scale)
    }

    /// Create a reflection across a line through the origin
    pub fn reflection(normal: Vector2<f64>) -> Self {
        let n = normal.normalize();
        let nx = n.x;
        let ny = n.y;
        
        let matrix = Matrix3::new(
            1.0 - 2.0 * nx * nx, -2.0 * nx * ny, 0.0,
            -2.0 * nx * ny, 1.0 - 2.0 * ny * ny, 0.0,
            0.0, 0.0, 1.0,
        );
        
        Self { matrix }
    }

    /// Create a reflection across the x-axis
    pub fn reflection_x() -> Self {
        Self::reflection(Vector2::new(0.0, 1.0))
    }

    /// Create a reflection across the y-axis
    pub fn reflection_y() -> Self {
        Self::reflection(Vector2::new(1.0, 0.0))
    }

    /// Create a reflection across a line defined by two points
    pub fn reflection_across_line(p1: Point2<f64>, p2: Point2<f64>) -> Self {
        let direction = p2 - p1;
        let normal = Vector2::new(-direction.y, direction.x).normalize();
        
        // Translate line to origin, reflect, then translate back
        let translate_to_origin = Self::translation(-p1.x, -p1.y);
        let reflect = Self::reflection(normal);
        let translate_back = Self::translation(p1.x, p1.y);
        
        translate_back.compose(&reflect).compose(&translate_to_origin)
    }

    /// Compose this transformation with another (this * other)
    pub fn compose(&self, other: &Transform2D) -> Self {
        Self {
            matrix: self.matrix * other.matrix,
        }
    }

    /// Apply this transformation to a point
    pub fn transform_point(&self, point: Point2<f64>) -> Point2<f64> {
        let homogeneous = nalgebra::Vector3::new(point.x, point.y, 1.0);
        let transformed = self.matrix * homogeneous;
        Point2::new(transformed.x, transformed.y)
    }

    /// Apply this transformation to a vector
    pub fn transform_vector(&self, vector: Vector2<f64>) -> Vector2<f64> {
        let homogeneous = nalgebra::Vector3::new(vector.x, vector.y, 0.0);
        let transformed = self.matrix * homogeneous;
        Vector2::new(transformed.x, transformed.y)
    }

    /// Get the inverse transformation
    pub fn inverse(&self) -> Option<Self> {
        self.matrix.try_inverse().map(|inv_matrix| Self {
            matrix: inv_matrix,
        })
    }

    /// Get the determinant (indicates scaling factor and orientation)
    pub fn determinant(&self) -> f64 {
        // For 2D transformations, we only care about the 2x2 part
        self.matrix[(0, 0)] * self.matrix[(1, 1)] - self.matrix[(0, 1)] * self.matrix[(1, 0)]
    }

    /// Check if this transformation preserves orientation (det > 0)
    pub fn preserves_orientation(&self) -> bool {
        self.determinant() > 0.0
    }

    /// Check if this transformation is a rigid transformation (preserves distances)
    pub fn is_rigid(&self) -> bool {
        let det = self.determinant();
        (det - 1.0).abs() < 1e-10 || (det + 1.0).abs() < 1e-10
    }
}

/// Symmetry operations for geometric objects
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum Symmetry {
    /// Reflection across a line
    Reflection { line_point1: Point2<f64>, line_point2: Point2<f64> },
    /// Rotation around a point
    Rotation { center: Point2<f64>, angle: f64 },
    /// Translation by a vector
    Translation { vector: Vector2<f64> },
    /// Point symmetry (180° rotation)
    PointSymmetry { center: Point2<f64> },
    /// Glide reflection (reflection + translation)
    GlideReflection { 
        line_point1: Point2<f64>, 
        line_point2: Point2<f64>, 
        translation: Vector2<f64> 
    },
}

impl Symmetry {
    /// Convert symmetry operation to transformation matrix
    pub fn to_transform(&self) -> Transform2D {
        match self {
            Symmetry::Reflection { line_point1, line_point2 } => {
                Transform2D::reflection_across_line(*line_point1, *line_point2)
            }
            Symmetry::Rotation { center, angle } => {
                Transform2D::rotation_around_point(*angle, *center)
            }
            Symmetry::Translation { vector } => {
                Transform2D::translation(vector.x, vector.y)
            }
            Symmetry::PointSymmetry { center } => {
                Transform2D::rotation_around_point(std::f64::consts::PI, *center)
            }
            Symmetry::GlideReflection { line_point1, line_point2, translation } => {
                let reflection = Transform2D::reflection_across_line(*line_point1, *line_point2);
                let translate = Transform2D::translation(translation.x, translation.y);
                translate.compose(&reflection)
            }
        }
    }

    /// Apply this symmetry operation to a point
    pub fn apply_to_point(&self, point: Point2<f64>) -> Point2<f64> {
        self.to_transform().transform_point(point)
    }
}

/// Find all symmetries of a regular polygon
pub fn regular_polygon_symmetries(center: Point2<f64>, n: usize) -> Vec<Symmetry> {
    let mut symmetries = Vec::new();

    // Rotational symmetries
    for i in 0..n {
        let angle = 2.0 * std::f64::consts::PI * (i as f64) / (n as f64);
        symmetries.push(Symmetry::Rotation { center, angle });
    }

    // Reflection symmetries
    if n % 2 == 0 {
        // Even n: n/2 reflections through vertices and n/2 through edge midpoints
        for i in 0..n {
            let angle = std::f64::consts::PI * (i as f64) / (n as f64);
            let point_on_line = Point2::new(
                center.x + angle.cos(),
                center.y + angle.sin(),
            );
            symmetries.push(Symmetry::Reflection {
                line_point1: center,
                line_point2: point_on_line,
            });
        }
    } else {
        // Odd n: n reflections through vertices
        for i in 0..n {
            let angle = 2.0 * std::f64::consts::PI * (i as f64) / (n as f64);
            let vertex = Point2::new(
                center.x + angle.cos(),
                center.y + angle.sin(),
            );
            symmetries.push(Symmetry::Reflection {
                line_point1: center,
                line_point2: vertex,
            });
        }
    }

    symmetries
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_abs_diff_eq;

    #[test]
    fn test_translation() {
        let transform = Transform2D::translation(3.0, 4.0);
        let point = Point2::new(1.0, 2.0);
        let transformed = transform.transform_point(point);
        
        assert_abs_diff_eq!(transformed.x, 4.0, epsilon = 1e-10);
        assert_abs_diff_eq!(transformed.y, 6.0, epsilon = 1e-10);
    }

    #[test]
    fn test_rotation() {
        let transform = Transform2D::rotation(std::f64::consts::PI / 2.0); // 90 degrees
        let point = Point2::new(1.0, 0.0);
        let transformed = transform.transform_point(point);
        
        assert_abs_diff_eq!(transformed.x, 0.0, epsilon = 1e-10);
        assert_abs_diff_eq!(transformed.y, 1.0, epsilon = 1e-10);
    }

    #[test]
    fn test_reflection_x() {
        let transform = Transform2D::reflection_x();
        let point = Point2::new(1.0, 2.0);
        let transformed = transform.transform_point(point);
        
        assert_abs_diff_eq!(transformed.x, 1.0, epsilon = 1e-10);
        assert_abs_diff_eq!(transformed.y, -2.0, epsilon = 1e-10);
    }

    #[test]
    fn test_composition() {
        let translate = Transform2D::translation(1.0, 1.0);
        let rotate = Transform2D::rotation(std::f64::consts::PI / 2.0);
        let composed = translate.compose(&rotate);
        
        let point = Point2::new(1.0, 0.0);
        let transformed = composed.transform_point(point);
        
        assert_abs_diff_eq!(transformed.x, 1.0, epsilon = 1e-10);
        assert_abs_diff_eq!(transformed.y, 2.0, epsilon = 1e-10);
    }

    #[test]
    fn test_inverse() {
        let transform = Transform2D::rotation(std::f64::consts::PI / 4.0);
        let inverse = transform.inverse().unwrap();
        let composed = transform.compose(&inverse);
        
        let point = Point2::new(1.0, 1.0);
        let transformed = composed.transform_point(point);
        
        assert_abs_diff_eq!(transformed.x, 1.0, epsilon = 1e-10);
        assert_abs_diff_eq!(transformed.y, 1.0, epsilon = 1e-10);
    }

    #[test]
    fn test_rigid_transformation() {
        let rotation = Transform2D::rotation(std::f64::consts::PI / 3.0);
        let translation = Transform2D::translation(2.0, 3.0);
        let reflection = Transform2D::reflection_x();
        
        assert!(rotation.is_rigid());
        assert!(translation.is_rigid());
        assert!(reflection.is_rigid());
        
        let scaling = Transform2D::scaling(2.0, 2.0);
        assert!(!scaling.is_rigid());
    }

    #[test]
    fn test_regular_polygon_symmetries() {
        let center = Point2::new(0.0, 0.0);
        let symmetries = regular_polygon_symmetries(center, 4); // Square
        
        // Should have 4 rotations + 4 reflections = 8 symmetries
        assert_eq!(symmetries.len(), 8);
        
        // Count rotations and reflections
        let rotations = symmetries.iter().filter(|s| matches!(s, Symmetry::Rotation { .. })).count();
        let reflections = symmetries.iter().filter(|s| matches!(s, Symmetry::Reflection { .. })).count();
        
        assert_eq!(rotations, 4);
        assert_eq!(reflections, 4);
    }
}