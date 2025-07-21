/*
 * NERV Geometry Engine - Server Binary
 *
 * Provides a command-line interface for the geometry engine
 * that can be called from Python via subprocess.
 */

use serde_json::{Value, json};
use std::io::{self, Read};

fn main() {
    env_logger::init();
    
    // Read JSON input from stdin
    let mut buffer = String::new();
    match io::stdin().read_to_string(&mut buffer) {
        Ok(_) => {
            if let Ok(command) = serde_json::from_str::<Value>(&buffer) {
                let response = process_command(command);
                println!("{}", serde_json::to_string(&response).unwrap());
            } else {
                println!("{}", json!({"error": "Invalid JSON input"}));
            }
        }
        Err(_) => {
            println!("{}", json!({"error": "Failed to read input"}));
        }
    }
}

fn process_command(command: Value) -> Value {
    let cmd_type = command.get("command").and_then(|v| v.as_str());
    
    match cmd_type {
        Some("health_check") => {
            json!({
                "status": "healthy",
                "version": env!("CARGO_PKG_VERSION"),
                "engine": "rust"
            })
        }
        
        Some("create_construction_space") => {
            json!({
                "construction_space": {
                    "points": {},
                    "lines": {},
                    "circles": {},
                    "history": []
                }
            })
        }
        
        Some("add_point") => {
            let x = command.get("x").and_then(|v| v.as_f64()).unwrap_or(0.0);
            let y = command.get("y").and_then(|v| v.as_f64()).unwrap_or(0.0);
            let label = command.get("label").and_then(|v| v.as_str()).unwrap_or("");
            
            // Generate a unique ID for the point
            let uuid_str = uuid::Uuid::new_v4().to_string();
            let point_id = format!("point_{}", &uuid_str[..8]);
            
            json!({
                "point_id": point_id,
                "construction_space": {
                    "points": {
                        point_id.clone(): {
                            "id": point_id,
                            "x": x,
                            "y": y,
                            "label": label
                        }
                    },
                    "lines": {},
                    "circles": {},
                    "history": [{
                        "action": "add_point",
                        "point_id": point_id,
                        "x": x,
                        "y": y,
                        "timestamp": chrono::Utc::now().to_rfc3339()
                    }]
                }
            })
        }
        
        Some("construct_line") => {
            let point1_id = command.get("point1_id").and_then(|v| v.as_str()).unwrap_or("");
            let point2_id = command.get("point2_id").and_then(|v| v.as_str()).unwrap_or("");
            let label = command.get("label").and_then(|v| v.as_str()).unwrap_or("");
            
            let uuid_str = uuid::Uuid::new_v4().to_string();
            let line_id = format!("line_{}", &uuid_str[..8]);
            
            json!({
                "line_id": line_id,
                "construction_space": {
                    "points": command.get("construction_space").unwrap_or(&json!({})).get("points").unwrap_or(&json!({})),
                    "lines": {
                        line_id.clone(): {
                            "id": line_id,
                            "point1_id": point1_id,
                            "point2_id": point2_id,
                            "label": label
                        }
                    },
                    "circles": {},
                    "history": []
                }
            })
        }
        
        Some("construct_circle") => {
            let center_id = command.get("center_id").and_then(|v| v.as_str()).unwrap_or("");
            let radius_point_id = command.get("radius_point_id").and_then(|v| v.as_str()).unwrap_or("");
            let label = command.get("label").and_then(|v| v.as_str()).unwrap_or("");
            
            let uuid_str = uuid::Uuid::new_v4().to_string();
            let circle_id = format!("circle_{}", &uuid_str[..8]);
            
            json!({
                "circle_id": circle_id,
                "construction_space": {
                    "points": command.get("construction_space").unwrap_or(&json!({})).get("points").unwrap_or(&json!({})),
                    "lines": command.get("construction_space").unwrap_or(&json!({})).get("lines").unwrap_or(&json!({})),
                    "circles": {
                        circle_id.clone(): {
                            "id": circle_id,
                            "center_id": center_id,
                            "radius_point_id": radius_point_id,
                            "label": label
                        }
                    },
                    "history": []
                }
            })
        }
        
        Some("find_intersections") => {
            let obj1_id = command.get("obj1_id").and_then(|v| v.as_str()).unwrap_or("");
            let obj2_id = command.get("obj2_id").and_then(|v| v.as_str()).unwrap_or("");
            
            // For now, return empty intersections
            // TODO: Implement actual intersection calculations
            json!({
                "intersections": [],
                "construction_space": command.get("construction_space").unwrap_or(&json!({
                    "points": {}, "lines": {}, "circles": {}, "history": []
                }))
            })
        }
        
        Some("validate_construction") => {
            json!({
                "is_valid": true,
                "errors": [],
                "suggestions": []
            })
        }
        
        _ => {
            json!({
                "error": format!("Unknown command: {:?}", cmd_type)
            })
        }
    }
}