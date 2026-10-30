use serde::Deserialize;

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Message {
    pub event: String,
    pub display: Option<[u32; 2]>,
    pub root: Option<Node>,
}
#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Node {
    #[serde(rename = "class")]
    pub kind: String,
    pub focused: bool,
    pub padding: [i32; 4],
    pub text: Option<String>,
    pub text_size: Option<f32>,
    pub orientation: Option<u8>,
    #[serde(default)]
    pub children: Vec<Node>,
}
impl Node {
    pub fn validate(&self, depth: usize, budget: &mut usize) -> Result<(), String> {
        if depth > 32 || *budget == 0 {
            return Err("View tree exceeds budget".into());
        }
        *budget -= 1;
        if self.padding.iter().any(|value| !(0..=8192).contains(value)) {
            return Err("Unsupported padding".into());
        }
        match self.kind.as_str() {
            "android.widget.LinearLayout" => {
                if !matches!(self.orientation, Some(0 | 1)) || self.text.is_some() {
                    return Err("Invalid LinearLayout".into());
                }
            }
            "android.widget.TextView" | "android.widget.Button" => {
                if !self.children.is_empty()
                    || self.text.as_ref().is_none_or(|text| text.len() > 32768)
                    || self
                        .text_size
                        .is_none_or(|size| !size.is_finite() || !(0.0..=1024.0).contains(&size))
                {
                    return Err("Invalid text view".into());
                }
            }
            _ => return Err(format!("Unsupported View type: {}", self.kind)),
        }
        for child in &self.children {
            child.validate(depth + 1, budget)?;
        }
        Ok(())
    }
}
