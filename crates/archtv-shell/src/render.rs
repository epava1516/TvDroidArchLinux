//! CPU UI renderer. All geometry uses a 1920×1080 design coordinate space.
use fontdue::{Font, FontSettings, Metrics};
use std::collections::HashMap;
use tiny_skia::{Color, FillRule, Paint, PathBuilder, Pixmap, Rect, Transform};

pub struct Canvas {
    pub pixmap: Pixmap,
    font: Font,
    glyphs: HashMap<(char, u16), (Metrics, Vec<u8>)>,
    scale: f32,
}
impl Canvas {
    pub fn scale(&self) -> f32 {
        self.scale
    }
    pub fn new(width: u32, height: u32, font: &[u8]) -> Result<Self, String> {
        Ok(Self {
            pixmap: Pixmap::new(width, height).ok_or("invalid canvas size")?,
            font: Font::from_bytes(font, FontSettings::default()).map_err(str::to_string)?,
            glyphs: HashMap::new(),
            scale: width as f32 / 1920.0,
        })
    }
    pub fn rect(&mut self, x: f32, y: f32, w: f32, h: f32, color: [u8; 4]) {
        // Axis-aligned rectangles land on physical pixels. At fractional scale,
        // antialiasing every background strip is both unnecessary and costly.
        let left = (x * self.scale).round();
        let top = (y * self.scale).round();
        let right = ((x + w) * self.scale).round();
        let bottom = ((y + h) * self.scale).round();
        if let Some(rect) = Rect::from_xywh(left, top, right - left, bottom - top) {
            let mut paint = Paint {
                anti_alias: false,
                ..Paint::default()
            };
            paint.set_color_rgba8(color[0], color[1], color[2], color[3]);
            self.pixmap
                .fill_rect(rect, &paint, Transform::identity(), None);
        }
    }
    pub fn rounded(&mut self, x: f32, y: f32, w: f32, h: f32, radius: f32, color: [u8; 4]) {
        let r = radius.min(w / 2.0).min(h / 2.0);
        let mut path = PathBuilder::new();
        path.move_to(x + r, y);
        path.line_to(x + w - r, y);
        path.quad_to(x + w, y, x + w, y + r);
        path.line_to(x + w, y + h - r);
        path.quad_to(x + w, y + h, x + w - r, y + h);
        path.line_to(x + r, y + h);
        path.quad_to(x, y + h, x, y + h - r);
        path.line_to(x, y + r);
        path.quad_to(x, y, x + r, y);
        path.close();
        if let Some(path) = path.finish() {
            let mut paint = Paint::default();
            paint.set_color_rgba8(color[0], color[1], color[2], color[3]);
            self.pixmap.fill_path(
                &path,
                &paint,
                FillRule::Winding,
                Transform::from_scale(self.scale, self.scale),
                None,
            );
        }
    }
    pub fn text(&mut self, text: &str, x: f32, baseline: f32, px: f32, color: [u8; 3]) {
        let size = (px * self.scale).round().max(1.0) as u16;
        let mut cursor = x * self.scale;
        let baseline = baseline * self.scale;
        let width = self.pixmap.width() as usize;
        let height = self.pixmap.height() as usize;
        for ch in text.chars() {
            let (metrics, bitmap) = self
                .glyphs
                .entry((ch, size))
                .or_insert_with(|| self.font.rasterize(ch, f32::from(size)));
            let left = cursor.round() as i32 + metrics.xmin;
            let top = baseline.round() as i32 - metrics.height as i32 - metrics.ymin;
            let bytes = self.pixmap.data_mut();
            for row in 0..metrics.height {
                let y = top + row as i32;
                if y < 0 || y as usize >= height {
                    continue;
                }
                for col in 0..metrics.width {
                    let x = left + col as i32;
                    if x < 0 || x as usize >= width {
                        continue;
                    }
                    let alpha = u32::from(bitmap[row * metrics.width + col]);
                    if alpha == 0 {
                        continue;
                    }
                    let offset = (y as usize * width + x as usize) * 4;
                    for c in 0..3 {
                        bytes[offset + c] = ((u32::from(color[c]) * alpha
                            + u32::from(bytes[offset + c]) * (255 - alpha)
                            + 127)
                            / 255) as u8;
                    }
                    bytes[offset + 3] = 255;
                }
            }
            cursor += metrics.advance_width;
        }
    }
    pub fn home_probe(&mut self, focus: usize) {
        self.pixmap.fill(Color::from_rgba8(14, 16, 22, 255));
        // Original vector art; no remote poster or catalogue is bundled.
        for band in 0..70 {
            let t = band as f32 / 69.0;
            self.rect(
                700.0 + band as f32 * 18.0,
                100.0,
                20.0,
                510.0,
                [
                    18 + (t * 12.0) as u8,
                    29 + (t * 34.0) as u8,
                    46 + (t * 48.0) as u8,
                    255,
                ],
            );
        }
        self.rounded(1180.0, 175.0, 500.0, 300.0, 150.0, [34, 88, 105, 255]);
        self.rounded(1280.0, 200.0, 320.0, 250.0, 125.0, [48, 129, 134, 255]);
        self.rect(0.0, 0.0, 1920.0, 115.0, [14, 16, 22, 255]);
        let navigation = ["Buscar", "Inicio", "Aplicaciones", "Recientes", "Ajustes"];
        let positions = [190.0, 390.0, 570.0, 880.0, 1130.0];
        self.text("≡", 80.0, 75.0, 40.0, [230, 232, 237]);
        for (i, label) in navigation.iter().enumerate() {
            if i == 1 {
                self.rounded(
                    positions[i] - 25.0,
                    31.0,
                    145.0,
                    57.0,
                    29.0,
                    [244, 245, 247, 255],
                );
            }
            self.text(
                label,
                positions[i],
                70.0,
                29.0,
                if i == 1 {
                    [20, 23, 29]
                } else {
                    [217, 220, 226]
                },
            );
        }
        self.text("ARCH TV", 1640.0, 70.0, 27.0, [221, 226, 234]);
        self.text("Tu televisión.", 85.0, 285.0, 68.0, [248, 249, 251]);
        self.text("A tu manera.", 85.0, 365.0, 68.0, [248, 249, 251]);
        self.text(
            "Aplicaciones Linux y Android, en una interfaz ligera.",
            88.0,
            420.0,
            26.0,
            [191, 199, 211],
        );
        self.rounded(88.0, 460.0, 285.0, 63.0, 32.0, [239, 241, 245, 255]);
        self.text("Mis aplicaciones", 113.0, 502.0, 27.0, [21, 25, 32]);
        self.text(
            "Vista del prototipo · sin catálogo de contenidos",
            88.0,
            565.0,
            22.0,
            [151, 164, 180],
        );
        let cards = [
            ("Aplicaciones Linux", [37, 71, 106, 255]),
            ("Android", [42, 93, 79, 255]),
            ("Tu biblioteca", [79, 53, 100, 255]),
            ("Preferencias", [106, 68, 43, 255]),
            ("Continuar", [54, 65, 88, 255]),
        ];
        for (i, (label, color)) in cards.iter().enumerate() {
            let x = 88.0 + i as f32 * 352.0;
            if i == focus {
                self.rounded(x - 5.0, 615.0, 332.0, 187.0, 22.0, [249, 250, 252, 255]);
            }
            self.rounded(x, 620.0, 322.0, 177.0, 18.0, *color);
            self.text(label, x + 22.0, 753.0, 29.0, [248, 249, 251]);
        }
        self.text("Tus aplicaciones", 88.0, 870.0, 28.0, [222, 227, 235]);
        let apps = [
            "Linux", "Android", "Archivos", "Música", "Vídeo", "Red", "Sonido", "Ajustes", "Todas",
        ];
        for (i, label) in apps.iter().enumerate() {
            let x = 88.0 + i as f32 * 192.0;
            self.rounded(x, 898.0, 168.0, 95.0, 17.0, [33, 39, 51, 255]);
            self.text(label, x + 17.0, 956.0, 24.0, [226, 232, 240]);
        }
    }
}
