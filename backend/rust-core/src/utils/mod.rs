//! Utility functions and helpers for the geometry engine

use nalgebra::{Point2, Vector2};
use serde::{Deserialize, Serialize};

/// Mathematical constants used throughout the geometry engine
pub mod constants {
    pub const EPSILON: f64 = 1e-10;
    pub const PI: f64 = std::f64::consts::PI;
    pub const TAU: f64 = 2.0 * std::f64::consts::PI;
    pub const GOLDEN_RATIO: f64 = 1.618033988749895;
    pub const SQRT_2: f64 = std::f64::consts::SQRT_2;
    pub const SQRT_3: f64 = 1.7320508075688772;
}

/// Floating point comparison utilities
pub mod float_utils {
    use super::constants::EPSILON;

    /// Check if two floating point numbers are approximately equal
    pub fn approx_eq(a: f64, b: f64) -> bool {
        (a - b).abs() < EPSILON
    }

    /// Check if two floating point numbers are approximately equal with custom tolerance
    pub fn approx_eq_tol(a: f64, b: f64, tolerance: f64) -> bool {
        (a - b).abs() < tolerance
    }

    /// Check if a floating point number is approximately zero
    pub fn approx_zero(a: f64) -> bool {
        a.abs() < EPSILON
    }

    /// Clamp a value between min and max
    pub fn clamp(value: f64, min: f64, max: f64) -> f64 {
        if value < min {
            min
        } else if value > max {
            max
        } else {
            value
        }
    }

    /// Round to specified number of decimal places
    pub fn round_to_places(value: f64, places: u32) -> f64 {
        let multiplier = 10_f64.powi(places as i32);
        (value * multiplier).round() / multiplier
    }
}

/// Angle utilities for geometric calculations
pub mod angle_utils {
    use super::constants::{PI, TAU};
    use nalgebra::{Point2, Vector2};

    /// Convert degrees to radians
    pub fn deg_to_rad(degrees: f64) -> f64 {
        degrees * PI / 180.0
    }

    /// Convert radians to degrees
    pub fn rad_to_deg(radians: f64) -> f64 {
        radians * 180.0 / PI
    }

    /// Normalize angle to [0, 2π)
    pub fn normalize_angle(angle: f64) -> f64 {
        let mut normalized = angle % TAU;
        if normalized < 0.0 {
            normalized += TAU;
        }
        normalized
    }

    /// Normalize angle to (-π, π]
    pub fn normalize_angle_signed(angle: f64) -> f64 {
        let mut normalized = angle % TAU;
        if normalized > PI {
            normalized -= TAU;
        } else if normalized <= -PI {
            normalized += TAU;
        }
        normalized
    }

    /// Calculate angle between two vectors
    pub fn angle_between_vectors(v1: Vector2<f64>, v2: Vector2<f64>) -> f64 {
        let dot = v1.dot(&v2);
        let lengths = v1.magnitude() * v2.magnitude();
        
        if lengths < super::constants::EPSILON {
            return 0.0;
        }
        
        (dot / lengths).acos()
    }

    /// Calculate angle of vector from positive x-axis
    pub fn vector_angle(vector: Vector2<f64>) -> f64 {
        vector.y.atan2(vector.x)
    }

    /// Calculate angle from three points (angle at middle point)
    pub fn angle_from_points(p1: Point2<f64>, vertex: Point2<f64>, p2: Point2<f64>) -> f64 {
        let v1 = p1 - vertex;
        let v2 = p2 - vertex;
        angle_between_vectors(v1, v2)
    }

    /// Check if angle is acute (< 90°)
    pub fn is_acute(angle: f64) -> bool {
        angle < PI / 2.0
    }

    /// Check if angle is obtuse (> 90°)
    pub fn is_obtuse(angle: f64) -> bool {
        angle > PI / 2.0
    }

    /// Check if angle is right (= 90°)
    pub fn is_right(angle: f64) -> bool {
        (angle - PI / 2.0).abs() < super::constants::EPSILON
    }
}

/// Color utilities for visualization
pub mod color_utils {
    use serde::{Deserialize, Serialize};

    #[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
    pub struct Color {
        pub r: u8,
        pub g: u8,
        pub b: u8,
        pub a: u8,
    }

    impl Color {
        /// Create a new color
        pub fn new(r: u8, g: u8, b: u8, a: u8) -> Self {
            Self { r, g, b, a }
        }

        /// Create color from RGB (full opacity)
        pub fn rgb(r: u8, g: u8, b: u8) -> Self {
            Self::new(r, g, b, 255)
        }

        /// Create color from hex string
        pub fn from_hex(hex: &str) -> Result<Self, String> {
            let hex = hex.trim_start_matches('#');
            
            if hex.len() != 6 && hex.len() != 8 {
                return Err("Hex color must be 6 or 8 characters".to_string());
            }

            let r = u8::from_str_radix(&hex[0..2], 16)
                .map_err(|_| "Invalid hex color")?;
            let g = u8::from_str_radix(&hex[2..4], 16)
                .map_err(|_| "Invalid hex color")?;
            let b = u8::from_str_radix(&hex[4..6], 16)
                .map_err(|_| "Invalid hex color")?;
            let a = if hex.len() == 8 {
                u8::from_str_radix(&hex[6..8], 16)
                    .map_err(|_| "Invalid hex color")?
            } else {
                255
            };

            Ok(Self::new(r, g, b, a))
        }

        /// Convert to hex string
        pub fn to_hex(&self) -> String {
            if self.a == 255 {
                format!("#{:02x}{:02x}{:02x}", self.r, self.g, self.b)
            } else {
                format!("#{:02x}{:02x}{:02x}{:02x}", self.r, self.g, self.b, self.a)
            }
        }

        /// Predefined colors for NERV interface
        pub const RED: Color = Color { r: 255, g: 72, b: 0, a: 255 };      // NERV Orange-Red
        pub const CYAN: Color = Color { r: 0, g: 255, b: 255, a: 255 };    // NERV Cyan
        pub const WHITE: Color = Color { r: 255, g: 255, b: 255, a: 255 };  // White
        pub const BLACK: Color = Color { r: 0, g: 0, b: 0, a: 255 };        // Black
        pub const GRAY: Color = Color { r: 170, g: 170, b: 170, a: 255 };   // Gray
    }
}

/// Performance measurement utilities
pub mod perf_utils {
    use std::time::{Duration, Instant};

    /// Simple performance timer
    pub struct Timer {
        start: Instant,
        label: String,
    }

    impl Timer {
        /// Create and start a new timer
        pub fn new(label: &str) -> Self {
            Self {
                start: Instant::now(),
                label: label.to_string(),
            }
        }

        /// Get elapsed time since timer creation
        pub fn elapsed(&self) -> Duration {
            self.start.elapsed()
        }

        /// Print elapsed time with label
        pub fn log_elapsed(&self) {
            log::debug!("{}: {:?}", self.label, self.elapsed());
        }
    }

    /// Time a function execution
    pub fn time_function<F, R>(label: &str, f: F) -> (R, Duration)
    where
        F: FnOnce() -> R,
    {
        let start = Instant::now();
        let result = f();
        let duration = start.elapsed();
        log::debug!("{}: {:?}", label, duration);
        (result, duration)
    }
}

/// Validation utilities for geometric constructions
pub mod validation {
    use super::constants::EPSILON;
    use nalgebra::Point2;

    /// Validate that a point has finite coordinates
    pub fn is_valid_point(point: &Point2<f64>) -> bool {
        point.x.is_finite() && point.y.is_finite()
    }

    /// Validate that points are not coincident
    pub fn points_are_distinct(p1: &Point2<f64>, p2: &Point2<f64>) -> bool {
        nalgebra::distance(p1, p2) > EPSILON
    }

    /// Validate that three points are not collinear
    pub fn points_not_collinear(p1: &Point2<f64>, p2: &Point2<f64>, p3: &Point2<f64>) -> bool {
        let area = 0.5 * ((p2.x - p1.x) * (p3.y - p1.y) - (p3.x - p1.x) * (p2.y - p1.y));
        area.abs() > EPSILON
    }

    /// Validate that a distance is positive
    pub fn is_positive_distance(distance: f64) -> bool {
        distance > EPSILON
    }

    /// Validate that an angle is in valid range [0, 2π]
    pub fn is_valid_angle(angle: f64) -> bool {
        angle >= 0.0 && angle <= 2.0 * std::f64::consts::PI + EPSILON
    }
}

/// String formatting utilities
pub mod format_utils {
    /// Format a floating point number for display
    pub fn format_float(value: f64, precision: usize) -> String {
        format!("{:.precision$}", value, precision = precision)
    }

    /// Format coordinates as a string
    pub fn format_point(x: f64, y: f64, precision: usize) -> String {
        format!("({}, {})", 
                format_float(x, precision), 
                format_float(y, precision))
    }

    /// Format angle in degrees with degree symbol
    pub fn format_angle_deg(angle_rad: f64, precision: usize) -> String {
        let degrees = angle_rad * 180.0 / std::f64::consts::PI;
        format!("{}°", format_float(degrees, precision))
    }

    /// Format distance with units
    pub fn format_distance(distance: f64, precision: usize, unit: &str) -> String {
        format!("{} {}", format_float(distance, precision), unit)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use nalgebra::{Point2, Vector2};

    #[test]
    fn test_float_approx_eq() {
        use float_utils::*;
        
        assert!(approx_eq(1.0, 1.0));
        assert!(approx_eq(1.0, 1.0 + constants::EPSILON / 2.0));
        assert!(!approx_eq(1.0, 1.1));
        
        assert!(approx_zero(0.0));
        assert!(approx_zero(constants::EPSILON / 2.0));
        assert!(!approx_zero(0.1));
    }

    #[test]
    fn test_angle_utils() {
        use angle_utils::*;
        
        assert!((deg_to_rad(180.0) - constants::PI).abs() < constants::EPSILON);
        assert!((rad_to_deg(constants::PI) - 180.0).abs() < constants::EPSILON);
        
        let normalized = normalize_angle(-constants::PI);
        assert!((normalized - constants::PI).abs() < constants::EPSILON);
        
        let v1 = Vector2::new(1.0, 0.0);
        let v2 = Vector2::new(0.0, 1.0);
        let angle = angle_between_vectors(v1, v2);
        assert!((angle - constants::PI / 2.0).abs() < constants::EPSILON);
    }

    #[test]
    fn test_color_from_hex() {
        use color_utils::*;
        
        let color = Color::from_hex("#FF4800").unwrap();
        assert_eq!(color.r, 255);
        assert_eq!(color.g, 72);
        assert_eq!(color.b, 0);
        assert_eq!(color.a, 255);
        
        let hex = color.to_hex();
        assert_eq!(hex, "#ff4800");
    }

    #[test]
    fn test_validation() {
        use validation::*;
        
        let p1 = Point2::new(0.0, 0.0);
        let p2 = Point2::new(1.0, 0.0);
        let p3 = Point2::new(2.0, 0.0);
        let p4 = Point2::new(0.0, 1.0);
        
        assert!(is_valid_point(&p1));
        assert!(points_are_distinct(&p1, &p2));
        assert!(!points_not_collinear(&p1, &p2, &p3)); // Collinear
        assert!(points_not_collinear(&p1, &p2, &p4)); // Not collinear
        
        assert!(is_positive_distance(1.0));
        assert!(!is_positive_distance(-1.0));
        assert!(!is_positive_distance(0.0));
        
        assert!(is_valid_angle(constants::PI));
        assert!(is_valid_angle(0.0));
        assert!(!is_valid_angle(-1.0));
    }

    #[test]
    fn test_format_utils() {
        use format_utils::*;
        
        assert_eq!(format_float(3.14159, 2), "3.14");
        assert_eq!(format_point(1.23, 4.56, 1), "(1.2, 4.6)");
        
        let angle_str = format_angle_deg(constants::PI / 2.0, 0);
        assert_eq!(angle_str, "90°");
        
        assert_eq!(format_distance(1.5, 1, "m"), "1.5 m");
    }
}