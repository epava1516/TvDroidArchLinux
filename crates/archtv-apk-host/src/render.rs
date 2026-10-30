use crate::model::Node;
use fontdue::{Font, FontSettings};
use tiny_skia::{Color, Paint, Pixmap, Rect, Transform};

pub struct Renderer {
    font: Font,
}
impl Renderer {
    pub fn new(bytes: Vec<u8>) -> Result<Self, String> {
        Ok(Self {
            font: Font::from_bytes(bytes, FontSettings::default()).map_err(str::to_string)?,
        })
    }
    fn size(&self, node: &Node) -> (f32, f32) {
        let [left, top, right, bottom] = node.padding.map(|value| value as f32);
        let (width, height) = if let Some(text) = &node.text {
            let px = node.text_size.unwrap_or(14.0).max(1.0);
            let width = text
                .chars()
                .map(|ch| self.font.metrics(ch, px).advance_width)
                .sum::<f32>();
            if node.kind == "android.widget.Button" {
                (width + 48.0, (px * 1.5 + 24.0).max(48.0))
            } else {
                (width, px * 1.5)
            }
        } else {
            node.children.iter().map(|child| self.size(child)).fold(
                (0.0_f32, 0.0_f32),
                |(w, h), (cw, ch)| {
                    if node.orientation == Some(0) {
                        (w + cw, h.max(ch))
                    } else {
                        (w.max(cw), h + ch)
                    }
                },
            )
        };
        (width + left + right, height + top + bottom)
    }
    pub fn render(&self, node: &Node, width: u32, height: u32) -> Result<Pixmap, String> {
        let mut pixmap = Pixmap::new(width, height).ok_or("Invalid render size")?;
        pixmap.fill(Color::from_rgba8(245, 245, 245, 255));
        self.node(&mut pixmap, node, 0.0, 0.0);
        Ok(pixmap)
    }
    fn rect(image: &mut Pixmap, x: f32, y: f32, width: f32, height: f32, color: [u8; 4]) {
        if let Some(rect) = Rect::from_xywh(x, y, width, height) {
            let mut paint = Paint::default();
            paint.set_color_rgba8(color[0], color[1], color[2], color[3]);
            image.fill_rect(rect, &paint, Transform::identity(), None);
        }
    }
    fn node(&self, image: &mut Pixmap, node: &Node, x: f32, y: f32) {
        let x = x + node.padding[0] as f32;
        let y = y + node.padding[1] as f32;
        if let Some(text) = &node.text {
            let size = node.text_size.unwrap_or(14.0).max(1.0);
            let button = node.kind == "android.widget.Button";
            let (width, height) = self.size(node);
            if button {
                Self::rect(
                    image,
                    x,
                    y,
                    width,
                    height,
                    if node.focused {
                        [20, 92, 178, 255]
                    } else {
                        [75, 95, 120, 255]
                    },
                );
                if node.focused {
                    Self::rect(image, x + 2.0, y + height - 4.0, width - 4.0, 2.0, [255; 4]);
                }
            }
            self.text(
                image,
                text,
                x + if button { 24.0 } else { 0.0 },
                y + size + if button { 12.0 } else { 0.0 },
                size,
                if button { [255; 3] } else { [24; 3] },
            );
        } else {
            let (mut child_x, mut child_y) = (x, y);
            for child in &node.children {
                self.node(image, child, child_x, child_y);
                let (width, height) = self.size(child);
                if node.orientation == Some(0) {
                    child_x += width;
                } else {
                    child_y += height;
                }
            }
        }
    }
    fn text(
        &self,
        image: &mut Pixmap,
        text: &str,
        mut x: f32,
        baseline: f32,
        size: f32,
        color: [u8; 3],
    ) {
        let width = image.width() as usize;
        let height = image.height() as usize;
        for character in text.chars() {
            let (metrics, pixels) = self.font.rasterize(character, size);
            let left = x.round() as i32 + metrics.xmin;
            let top = baseline.round() as i32 - metrics.height as i32 - metrics.ymin;
            for row in 0..metrics.height {
                let y = top + row as i32;
                if y < 0 || y as usize >= height {
                    continue;
                }
                for column in 0..metrics.width {
                    let px = left + column as i32;
                    if px < 0 || px as usize >= width {
                        continue;
                    }
                    let alpha = u32::from(pixels[row * metrics.width + column]);
                    let offset = (y as usize * width + px as usize) * 4;
                    let bytes = image.data_mut();
                    for c in 0..3 {
                        bytes[offset + c] = ((u32::from(color[c]) * alpha
                            + u32::from(bytes[offset + c]) * (255 - alpha)
                            + 127)
                            / 255) as u8;
                    }
                }
            }
            x += metrics.advance_width;
            if x > width as f32 {
                break;
            }
        }
    }
}
