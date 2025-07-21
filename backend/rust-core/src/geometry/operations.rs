//! Geometric operations for intersection calculations and construction validation

use super::{Point, Line, Circle};
use nalgebra::{Point2, Vector2};
use crate::{GeometryError, Result};

/// Calculate intersections between two lines
pub fn line_line_intersection(
    line1: &Line,
    p1a: &Point,
    p1b: &Point,
    line2: &Line,
    p2a: &Point,
    p2b: &Point,
) -> Result<Vec<Point>> {
    let dir1 = p1b.position - p1a.position;
    let dir2 = p2b.position - p2a.position;
    
    // Check if lines are parallel
    let determinant = dir1.x * dir2.y - dir1.y * dir2.x;
    if determinant.abs() < 1e-10 {
        return Ok(Vec::new()); // Parallel lines (no intersection or infinite intersections)
    }
    
    let diff = p2a.position - p1a.position;
    let t = (diff.x * dir2.y - diff.y * dir2.x) / determinant;
    
    let intersection_point = p1a.position + t * dir1;
    
    let point = Point::constructed(
        intersection_point.x,
        intersection_point.y,
        None,
        vec![line1.id.clone(), line2.id.clone()],
    );
    
    Ok(vec![point])
}

/// Calculate intersections between a line and a circle
pub fn line_circle_intersection(
    line: &Line,
    p1: &Point,
    p2: &Point,
    circle: &Circle,
    center: &Point,
    radius_point: &Point,
) -> Result<Vec<Point>> {
    let radius = center.distance_to(radius_point);
    let dir = (p2.position - p1.position).normalize();
    let to_center = center.position - p1.position;
    
    // Project center onto line
    let projection_length = to_center.dot(&dir);
    let closest_point = p1.position + projection_length * dir;
    let distance_to_line = nalgebra::distance(&center.position, &closest_point);
    
    if distance_to_line > radius + 1e-10 {
        return Ok(Vec::new()); // No intersection
    }
    
    let mut intersections = Vec::new();
    
    if (distance_to_line - radius).abs() < 1e-10 {
        // Tangent - one intersection
        let point = Point::constructed(
            closest_point.x,
            closest_point.y,
            None,
            vec![line.id.clone(), circle.id.clone()],
        );
        intersections.push(point);
    } else if distance_to_line < radius {
        // Two intersections
        let chord_half_length = (radius * radius - distance_to_line * distance_to_line).sqrt();
        
        let intersection1 = closest_point + chord_half_length * dir;
        let intersection2 = closest_point - chord_half_length * dir;
        
        let point1 = Point::constructed(
            intersection1.x,
            intersection1.y,
            None,
            vec![line.id.clone(), circle.id.clone()],
        );
        
        let point2 = Point::constructed(
            intersection2.x,
            intersection2.y,
            None,
            vec![line.id.clone(), circle.id.clone()],
        );
        
        intersections.push(point1);
        intersections.push(point2);
    }
    
    Ok(intersections)
}

/// Calculate intersections between two circles
pub fn circle_circle_intersection(
    circle1: &Circle,
    center1: &Point,
    radius_point1: &Point,
    circle2: &Circle,
    center2: &Point,
    radius_point2: &Point,
) -> Result<Vec<Point>> {
    let r1 = center1.distance_to(radius_point1);
    let r2 = center2.distance_to(radius_point2);
    let d = center1.distance_to(center2);
    
    // Check for no intersection cases
    if d > r1 + r2 + 1e-10 {
        return Ok(Vec::new()); // Circles too far apart
    }
    if d < (r1 - r2).abs() - 1e-10 {
        return Ok(Vec::new()); // One circle inside the other
    }
    if d < 1e-10 && (r1 - r2).abs() < 1e-10 {
        return Ok(Vec::new()); // Identical circles (infinite intersections)
    }
    
    let mut intersections = Vec::new();
    
    // Calculate intersection points
    let a = (r1 * r1 - r2 * r2 + d * d) / (2.0 * d);
    let h = (r1 * r1 - a * a).sqrt();
    
    // Point on line between centers
    let direction = (center2.position - center1.position) / d;
    let p = center1.position + a * direction;
    
    if h.abs() < 1e-10 {
        // One intersection (tangent)
        let point = Point::constructed(
            p.x,
            p.y,
            None,
            vec![circle1.id.clone(), circle2.id.clone()],
        );
        intersections.push(point);
    } else {
        // Two intersections
        let perpendicular = Vector2::new(-direction.y, direction.x);
        
        let intersection1 = p + h * perpendicular;
        let intersection2 = p - h * perpendicular;
        
        let point1 = Point::constructed(
            intersection1.x,
            intersection1.y,
            None,
            vec![circle1.id.clone(), circle2.id.clone()],
        );
        
        let point2 = Point::constructed(
            intersection2.x,
            intersection2.y,
            None,
            vec![circle1.id.clone(), circle2.id.clone()],
        );
        
        intersections.push(point1);
        intersections.push(point2);
    }
    
    Ok(intersections)
}

/// Check if three points are collinear
pub fn are_collinear(p1: &Point, p2: &Point, p3: &Point, tolerance: f64) -> bool {
    let area = 0.5 * ((p2.position.x - p1.position.x) * (p3.position.y - p1.position.y)
                    - (p3.position.x - p1.position.x) * (p2.position.y - p1.position.y));
    area.abs() < tolerance
}

/// Calculate the perpendicular bisector of two points
pub fn perpendicular_bisector(p1: &Point, p2: &Point) -> Result<(Point2<f64>, Vector2<f64>)> {
    let midpoint = Point2::new(
        (p1.position.x + p2.position.x) / 2.0,
        (p1.position.y + p2.position.y) / 2.0,
    );
    
    let direction = p2.position - p1.position;
    let perpendicular = Vector2::new(-direction.y, direction.x).normalize();
    
    Ok((midpoint, perpendicular))
}

/// Calculate the angle bisector of three points
pub fn angle_bisector(p1: &Point, vertex: &Point, p2: &Point) -> Result<Vector2<f64>> {
    let v1 = (p1.position - vertex.position).normalize();
    let v2 = (p2.position - vertex.position).normalize();
    
    let bisector = (v1 + v2).normalize();
    Ok(bisector)
}

/// Calculate the circumcenter of three points (center of circumscribed circle)
pub fn circumcenter(p1: &Point, p2: &Point, p3: &Point) -> Result<Point> {
    // Check if points are collinear
    if are_collinear(p1, p2, p3, 1e-10) {
        return Err(GeometryError::InvalidConstruction {
            reason: "Cannot find circumcenter of collinear points".to_string(),
        });
    }
    
    let ax = p1.position.x;
    let ay = p1.position.y;
    let bx = p2.position.x;
    let by = p2.position.y;
    let cx = p3.position.x;
    let cy = p3.position.y;
    
    let d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by));
    
    let ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d;
    let uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d;
    
    Ok(Point::constructed(
        ux,
        uy,
        Some("Circumcenter".to_string()),
        vec![p1.id.clone(), p2.id.clone(), p3.id.clone()],
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_abs_diff_eq;

    #[test]
    fn test_line_line_intersection() {
        let p1 = Point::new(0.0, 0.0, None);
        let p2 = Point::new(2.0, 0.0, None);
        let p3 = Point::new(1.0, -1.0, None);
        let p4 = Point::new(1.0, 1.0, None);
        
        let line1 = Line::new(p1.id.clone(), p2.id.clone(), None);
        let line2 = Line::new(p3.id.clone(), p4.id.clone(), None);
        
        let intersections = line_line_intersection(&line1, &p1, &p2, &line2, &p3, &p4).unwrap();
        
        assert_eq!(intersections.len(), 1);
        assert_abs_diff_eq!(intersections[0].position.x, 1.0, epsilon = 1e-10);
        assert_abs_diff_eq!(intersections[0].position.y, 0.0, epsilon = 1e-10);
    }

    #[test]
    fn test_circumcenter() {
        // Right triangle with circumcenter at hypotenuse midpoint
        let p1 = Point::new(0.0, 0.0, None);
        let p2 = Point::new(4.0, 0.0, None);
        let p3 = Point::new(0.0, 3.0, None);
        
        let center = circumcenter(&p1, &p2, &p3).unwrap();
        
        assert_abs_diff_eq!(center.position.x, 2.0, epsilon = 1e-10);
        assert_abs_diff_eq!(center.position.y, 1.5, epsilon = 1e-10);
    }

    #[test]
    fn test_collinearity() {
        let p1 = Point::new(0.0, 0.0, None);
        let p2 = Point::new(1.0, 1.0, None);
        let p3 = Point::new(2.0, 2.0, None);
        
        assert!(are_collinear(&p1, &p2, &p3, 1e-10));
        
        let p4 = Point::new(2.0, 1.0, None);
        assert!(!are_collinear(&p1, &p2, &p4, 1e-10));
    }
}