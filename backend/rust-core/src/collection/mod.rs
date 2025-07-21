//! Collection system for geometric elements (Pokédex-style mechanics)

use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use uuid::Uuid;

/// Represents a caught geometric element in the collection
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CollectedElement {
    pub id: String,
    pub element_type: ElementType,
    pub name: String,
    pub description: String,
    pub rarity: Rarity,
    pub stats: ElementStats,
    pub unlock_requirements: Vec<String>,
    pub unlocks: Vec<String>,
    pub caught_at: chrono::DateTime<chrono::Utc>,
}

/// Types of geometric elements that can be collected
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum ElementType {
    /// Basic point element
    Point,
    /// Line segment or infinite line
    Line { finite: bool },
    /// Circle with various properties
    Circle { filled: bool },
    /// Angle between two lines
    Angle,
    /// Triangle with classification
    Triangle { triangle_type: TriangleType },
    /// Polygon with n sides
    Polygon { sides: usize },
    /// Geometric construction/proposition
    Construction { proposition_number: Option<usize> },
    /// Transformation operation
    Transformation { transform_type: TransformationType },
}

/// Triangle classifications for collection system
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum TriangleType {
    Scalene,
    Isosceles,
    Equilateral,
    Right,
    Acute,
    Obtuse,
}

/// Transformation types
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum TransformationType {
    Translation,
    Rotation,
    Reflection,
    Scaling,
    Glide,
}

/// Rarity levels for elements
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum Rarity {
    Common,
    Uncommon,
    Rare,
    Epic,
    Legendary,
    Mythic,
}

/// Stats for geometric elements (like Pokemon stats)
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ElementStats {
    pub precision: u8,    // How precisely it can be constructed
    pub complexity: u8,   // How complex constructions it can perform
    pub elegance: u8,     // How elegant the construction is
    pub power: u8,        // How many other elements it can help construct
    pub rarity_score: u8, // Numerical rarity value
}

/// Collection system that tracks caught elements
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ElementCollection {
    pub elements: HashMap<String, CollectedElement>,
    pub discovered: HashSet<String>, // Elements seen but not caught
    pub caught_count: usize,
    pub seen_count: usize,
    pub completion_percentage: f32,
}

impl ElementCollection {
    /// Create a new empty collection
    pub fn new() -> Self {
        Self {
            elements: HashMap::new(),
            discovered: HashSet::new(),
            caught_count: 0,
            seen_count: 0,
            completion_percentage: 0.0,
        }
    }

    /// Add a new element to the collection
    pub fn catch_element(&mut self, element: CollectedElement) -> bool {
        if self.elements.contains_key(&element.id) {
            return false; // Already caught
        }

        self.elements.insert(element.id.clone(), element);
        self.caught_count += 1;
        self.update_completion();
        true
    }

    /// Mark an element as seen (discovered but not caught)
    pub fn discover_element(&mut self, element_id: String) -> bool {
        if self.elements.contains_key(&element_id) || self.discovered.contains(&element_id) {
            return false; // Already caught or seen
        }

        self.discovered.insert(element_id);
        self.seen_count += 1;
        self.update_completion();
        true
    }

    /// Get available construction tools based on collection
    pub fn get_available_tools(&self) -> Vec<ConstructionTool> {
        let mut tools = vec![
            ConstructionTool::Point, // Always available
        ];

        // Check if we have the required elements for each tool
        if self.has_element_type(&ElementType::Point) {
            tools.push(ConstructionTool::Line);
            tools.push(ConstructionTool::Circle);
        }

        if self.has_element_type(&ElementType::Line { finite: false }) {
            tools.push(ConstructionTool::Intersection);
            tools.push(ConstructionTool::Perpendicular);
            tools.push(ConstructionTool::Parallel);
        }

        if self.has_element_type(&ElementType::Circle { filled: false }) {
            tools.push(ConstructionTool::Tangent);
            tools.push(ConstructionTool::Arc);
        }

        if self.has_construction(1) { // Euclid's first proposition (equilateral triangle)
            tools.push(ConstructionTool::EquilateralTriangle);
        }

        tools
    }

    /// Check if collection has a specific element type
    pub fn has_element_type(&self, element_type: &ElementType) -> bool {
        self.elements.values().any(|e| &e.element_type == element_type)
    }

    /// Check if collection has a specific construction/proposition
    pub fn has_construction(&self, proposition_number: usize) -> bool {
        self.elements.values().any(|e| {
            matches!(e.element_type, ElementType::Construction { proposition_number: Some(n) } if n == proposition_number)
        })
    }

    /// Get elements by rarity
    pub fn get_by_rarity(&self, rarity: Rarity) -> Vec<&CollectedElement> {
        self.elements.values().filter(|e| e.rarity == rarity).collect()
    }

    /// Get total power level of collection
    pub fn total_power(&self) -> u32 {
        self.elements.values().map(|e| e.stats.power as u32).sum()
    }

    /// Get elements that can be used for a specific construction
    pub fn elements_for_construction(&self, _construction_type: &str) -> Vec<&CollectedElement> {
        // This would contain logic for which elements are needed for specific constructions
        self.elements.values().collect() // Simplified for now
    }

    /// Update completion percentage
    fn update_completion(&mut self) {
        let total_possible = 100; // This would be the total number of collectible elements
        let total_found = self.caught_count + self.seen_count;
        self.completion_percentage = (total_found as f32 / total_possible as f32) * 100.0;
    }

    /// Get collection statistics
    pub fn get_stats(&self) -> CollectionStats {
        let mut rarity_counts = HashMap::new();
        for element in self.elements.values() {
            *rarity_counts.entry(element.rarity.clone()).or_insert(0) += 1;
        }

        CollectionStats {
            total_caught: self.caught_count,
            total_seen: self.seen_count,
            completion_percentage: self.completion_percentage,
            rarity_counts,
            total_power: self.total_power(),
            favorite_element: self.get_strongest_element().map(|e| e.name.clone()),
        }
    }

    /// Get the strongest element in collection
    pub fn get_strongest_element(&self) -> Option<&CollectedElement> {
        self.elements.values().max_by_key(|e| e.stats.power)
    }
}

/// Available construction tools based on collection
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum ConstructionTool {
    Point,
    Line,
    Circle,
    Intersection,
    Perpendicular,
    Parallel,
    Tangent,
    Arc,
    EquilateralTriangle,
    Square,
    RegularPolygon { sides: usize },
    AngleBisector,
    PerpendicularBisector,
}

/// Collection statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CollectionStats {
    pub total_caught: usize,
    pub total_seen: usize,
    pub completion_percentage: f32,
    pub rarity_counts: HashMap<Rarity, usize>,
    pub total_power: u32,
    pub favorite_element: Option<String>,
}

/// Factory for creating standard geometric elements
pub struct ElementFactory;

impl ElementFactory {
    /// Create a basic point element
    pub fn create_point() -> CollectedElement {
        CollectedElement {
            id: Uuid::new_v4().to_string(),
            element_type: ElementType::Point,
            name: "Point".to_string(),
            description: "The fundamental element of geometry - a location with no size".to_string(),
            rarity: Rarity::Common,
            stats: ElementStats {
                precision: 100,
                complexity: 10,
                elegance: 50,
                power: 20,
                rarity_score: 1,
            },
            unlock_requirements: vec![],
            unlocks: vec!["Line".to_string(), "Circle".to_string()],
            caught_at: chrono::Utc::now(),
        }
    }

    /// Create a line element
    pub fn create_line() -> CollectedElement {
        CollectedElement {
            id: Uuid::new_v4().to_string(),
            element_type: ElementType::Line { finite: false },
            name: "Line".to_string(),
            description: "Infinite straight path connecting two points".to_string(),
            rarity: Rarity::Common,
            stats: ElementStats {
                precision: 90,
                complexity: 30,
                elegance: 70,
                power: 40,
                rarity_score: 2,
            },
            unlock_requirements: vec!["Point".to_string()],
            unlocks: vec!["Triangle".to_string(), "Polygon".to_string()],
            caught_at: chrono::Utc::now(),
        }
    }

    /// Create a circle element
    pub fn create_circle() -> CollectedElement {
        CollectedElement {
            id: Uuid::new_v4().to_string(),
            element_type: ElementType::Circle { filled: false },
            name: "Circle".to_string(),
            description: "Perfect round shape with all points equidistant from center".to_string(),
            rarity: Rarity::Uncommon,
            stats: ElementStats {
                precision: 95,
                complexity: 50,
                elegance: 90,
                power: 60,
                rarity_score: 3,
            },
            unlock_requirements: vec!["Point".to_string()],
            unlocks: vec!["Arc".to_string(), "Tangent".to_string()],
            caught_at: chrono::Utc::now(),
        }
    }

    /// Create Euclid's first proposition (equilateral triangle)
    pub fn create_equilateral_triangle() -> CollectedElement {
        CollectedElement {
            id: Uuid::new_v4().to_string(),
            element_type: ElementType::Construction { proposition_number: Some(1) },
            name: "Proposition I: Equilateral Triangle".to_string(),
            description: "Euclid's first proposition - construct an equilateral triangle on a given finite straight line".to_string(),
            rarity: Rarity::Rare,
            stats: ElementStats {
                precision: 85,
                complexity: 70,
                elegance: 95,
                power: 80,
                rarity_score: 4,
            },
            unlock_requirements: vec!["Point".to_string(), "Line".to_string(), "Circle".to_string()],
            unlocks: vec!["Triangle".to_string(), "Regular Polygon".to_string()],
            caught_at: chrono::Utc::now(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_collection() {
        let collection = ElementCollection::new();
        assert_eq!(collection.caught_count, 0);
        assert_eq!(collection.seen_count, 0);
        assert_eq!(collection.completion_percentage, 0.0);
    }

    #[test]
    fn test_catch_element() {
        let mut collection = ElementCollection::new();
        let point = ElementFactory::create_point();
        
        assert!(collection.catch_element(point.clone()));
        assert_eq!(collection.caught_count, 1);
        assert!(!collection.catch_element(point)); // Can't catch same element twice
    }

    #[test]
    fn test_discover_element() {
        let mut collection = ElementCollection::new();
        let element_id = "test_element".to_string();
        
        assert!(collection.discover_element(element_id.clone()));
        assert_eq!(collection.seen_count, 1);
        assert!(!collection.discover_element(element_id)); // Can't discover twice
    }

    #[test]
    fn test_available_tools() {
        let mut collection = ElementCollection::new();
        let initial_tools = collection.get_available_tools();
        assert_eq!(initial_tools, vec![ConstructionTool::Point]);
        
        // Add a point element
        let point = ElementFactory::create_point();
        collection.catch_element(point);
        
        let tools_with_point = collection.get_available_tools();
        assert!(tools_with_point.contains(&ConstructionTool::Line));
        assert!(tools_with_point.contains(&ConstructionTool::Circle));
    }

    #[test]
    fn test_element_factory() {
        let point = ElementFactory::create_point();
        assert_eq!(point.element_type, ElementType::Point);
        assert_eq!(point.name, "Point");
        assert_eq!(point.rarity, Rarity::Common);

        let line = ElementFactory::create_line();
        assert_eq!(line.element_type, ElementType::Line { finite: false });
        assert_eq!(line.rarity, Rarity::Common);

        let circle = ElementFactory::create_circle();
        assert_eq!(circle.element_type, ElementType::Circle { filled: false });
        assert_eq!(circle.rarity, Rarity::Uncommon);
    }

    #[test]
    fn test_collection_stats() {
        let mut collection = ElementCollection::new();
        
        let point = ElementFactory::create_point();
        let line = ElementFactory::create_line();
        let circle = ElementFactory::create_circle();
        
        collection.catch_element(point);
        collection.catch_element(line);
        collection.catch_element(circle);
        
        let stats = collection.get_stats();
        assert_eq!(stats.total_caught, 3);
        assert!(stats.total_power > 0);
        assert!(stats.favorite_element.is_some());
    }
}