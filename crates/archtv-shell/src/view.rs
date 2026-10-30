use crate::{
    model::{KEYBOARD, Model, Page, SETTING_ITEMS},
    render::Canvas,
};
use std::collections::HashMap;
use tiny_skia::Pixmap;
fn short(text: &str, max: usize) -> String {
    let mut value: String = text.chars().take(max).collect();
    if text.chars().count() > max {
        value.push('…');
    }
    value
}
impl Canvas {
    pub fn image(&mut self, image: &Pixmap, x: f32, y: f32, size: f32) {
        let scale = self.scale();
        let factor = (size / image.width() as f32).min(size / image.height() as f32) * scale;
        let transform =
            tiny_skia::Transform::from_scale(factor, factor).post_translate(x * scale, y * scale);
        self.pixmap.draw_pixmap(
            0,
            0,
            image.as_ref(),
            &tiny_skia::PixmapPaint::default(),
            transform,
            None,
        );
    }
    pub fn application(
        &mut self,
        model: &Model,
        icons: &HashMap<String, Option<Pixmap>>,
        app: &archtv_core::desktop::Application,
        position: (f32, f32),
        wide: bool,
        selected: bool,
    ) {
        let (x, y) = position;
        let (w, h) = if wide { (322.0, 175.0) } else { (322.0, 155.0) };
        if selected {
            self.rounded(
                x - 6.0,
                y - 6.0,
                w + 12.0,
                h + 12.0,
                22.0,
                model.focus_color(),
            );
        }
        let hue = app.id.bytes().fold(0u8, u8::wrapping_add);
        self.rounded(
            x,
            y,
            w,
            h,
            18.0,
            [27 + hue / 10, 35 + hue / 12, 48 + hue / 8, 255],
        );
        if let Some(Some(icon)) = icons.get(&app.id) {
            self.image(icon, x + (w - 76.0) / 2.0, y + 14.0, 76.0);
        } else {
            self.rounded(
                x + (w - 60.0) / 2.0,
                y + 22.0,
                60.0,
                60.0,
                15.0,
                [58, 74, 94, 255],
            );
            self.text(
                &app.name
                    .chars()
                    .next()
                    .unwrap_or('?')
                    .to_uppercase()
                    .to_string(),
                x + w / 2.0 - 13.0,
                y + 66.0,
                34.0,
                [240, 244, 250],
            );
        }
        self.text(
            &short(&app.name, 23),
            x + 18.0,
            y + h - 25.0,
            25.0,
            [240, 243, 249],
        );
        if model.settings.favorites.contains(&app.id) {
            self.text("★", x + w - 35.0, y + 35.0, 23.0, [255, 218, 130]);
        }
    }
    pub fn shell(&mut self, model: &Model, icons: &HashMap<String, Option<Pixmap>>) {
        self.pixmap
            .fill(tiny_skia::Color::from_rgba8(14, 16, 22, 255));
        let navigation = ["Buscar", "Inicio", "Aplicaciones", "Recientes", "Ajustes"];
        let positions = [190.0, 390.0, 570.0, 880.0, 1130.0];
        let widths = [150.0, 145.0, 270.0, 220.0, 185.0];
        self.text("≡", 80.0, 75.0, 40.0, [230, 232, 237]);
        for (index, label) in navigation.iter().enumerate() {
            let selected = index == model.page.index();
            if selected {
                self.rounded(
                    positions[index] - 25.0,
                    31.0,
                    widths[index],
                    57.0,
                    29.0,
                    if model.band == 0 {
                        model.focus_color()
                    } else {
                        [59, 66, 79, 255]
                    },
                );
            }
            self.text(
                label,
                positions[index],
                70.0,
                29.0,
                if selected && model.band == 0 {
                    [20, 23, 29]
                } else {
                    [224, 229, 237]
                },
            );
        }
        self.text("ARCH TV", 1640.0, 70.0, 27.0, [221, 226, 234]);
        match model.page {
            Page::Home => self.home(model, icons),
            Page::Apps | Page::Recent => {
                self.text(
                    if model.page == Page::Apps {
                        "Tus aplicaciones"
                    } else {
                        "Abiertas recientemente"
                    },
                    88.0,
                    185.0,
                    43.0,
                    [244, 247, 250],
                );
                self.text(
                    "Mantén Seleccionar o pulsa Menú para organizar",
                    90.0,
                    235.0,
                    23.0,
                    [172, 185, 203],
                );
                let apps = model.row(1);
                let start = if model.band > 0 {
                    (model.index / 5).saturating_sub(2) * 5
                } else {
                    0
                };
                if apps.is_empty() {
                    self.text(
                        if model.loading {
                            "Buscando aplicaciones…"
                        } else {
                            "No hay aplicaciones en esta sección"
                        },
                        90.0,
                        380.0,
                        29.0,
                        [204, 214, 229],
                    );
                }
                for (position, app) in apps.iter().enumerate().skip(start).take(20) {
                    let cell = position - start;
                    self.application(
                        model,
                        icons,
                        app,
                        (
                            88.0 + (cell % 5) as f32 * 352.0,
                            290.0 + (cell / 5) as f32 * 176.0,
                        ),
                        false,
                        model.band > 0 && model.index == position,
                    );
                }
            }
            Page::Search => self.search(model, icons),
            Page::Settings => self.settings(model),
        }
        self.rect(0.0, 1020.0, 1920.0, 60.0, [14, 16, 22, 255]);
        self.text(
            &short(&model.notice, 116),
            88.0,
            1059.0,
            21.0,
            [175, 191, 210],
        );
        if model.context.is_some() {
            self.context(model);
        }
    }
    fn home(&mut self, model: &Model, icons: &HashMap<String, Option<Pixmap>>) {
        for band in 0..70 {
            let t = band as f32 / 69.0;
            self.rect(
                700.0 + band as f32 * 18.0,
                115.0,
                20.0,
                485.0,
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
        if let Some(app) = model.selected() {
            self.text(&short(&app.name, 23), 88.0, 300.0, 58.0, [248, 249, 251]);
            self.text(&short(&app.comment, 64), 90.0, 365.0, 25.0, [199, 210, 225]);
            self.text(
                if app.android {
                    "Aplicación Android · requiere sesión disponible"
                } else {
                    "Aplicación Linux instalada"
                },
                90.0,
                415.0,
                24.0,
                [170, 190, 208],
            );
            if let Some(Some(icon)) = icons.get(&app.id) {
                self.image(icon, 1320.0, 240.0, 180.0);
            }
        } else {
            self.text("Tu televisión.", 88.0, 275.0, 68.0, [248, 249, 251]);
            self.text("A tu manera.", 88.0, 355.0, 68.0, [248, 249, 251]);
            self.text(
                "Tu biblioteca de aplicaciones Linux y Android",
                90.0,
                415.0,
                25.0,
                [191, 204, 220],
            );
        }
        if model.band == 1 {
            self.rounded(82.0, 454.0, 296.0, 75.0, 36.0, [255, 255, 255, 255]);
        }
        self.rounded(
            88.0,
            460.0,
            284.0,
            63.0,
            31.0,
            if model.band == 1 {
                [255, 216, 139, 255]
            } else {
                [233, 237, 244, 255]
            },
        );
        self.text("Mis aplicaciones", 112.0, 502.0, 27.0, [20, 24, 31]);
        self.text(
            if model.settings.favorites.is_empty() {
                "Aplicaciones destacadas"
            } else {
                "Tus favoritas"
            },
            88.0,
            587.0,
            25.0,
            [218, 226, 238],
        );
        let row = model.row(2);
        let start = if model.band == 2 {
            model.index.saturating_sub(3)
        } else {
            0
        };
        for (index, app) in row.iter().enumerate().skip(start).take(5) {
            self.application(
                model,
                icons,
                app,
                (88.0 + (index - start) as f32 * 352.0, 615.0),
                true,
                model.band == 2 && model.index == index,
            );
        }
        if row.is_empty() {
            self.text(
                if model.loading {
                    "Buscando aplicaciones…"
                } else {
                    "No se encontraron aplicaciones gráficas"
                },
                90.0,
                710.0,
                30.0,
                [208, 218, 231],
            );
        }
        self.text("Todas tus aplicaciones", 88.0, 861.0, 26.0, [222, 227, 235]);
        let row = model.row(3);
        let start = if model.band == 3 {
            model.index.saturating_sub(7)
        } else {
            0
        };
        for (index, app) in row.iter().enumerate().skip(start).take(9) {
            let x = 88.0 + (index - start) as f32 * 192.0;
            if model.band == 3 && model.index == index {
                self.rounded(x - 5.0, 884.0, 178.0, 105.0, 21.0, model.focus_color());
            }
            self.rounded(x, 889.0, 168.0, 95.0, 17.0, [33, 39, 51, 255]);
            if let Some(Some(icon)) = icons.get(&app.id) {
                self.image(icon, x + 54.0, 899.0, 48.0);
            } else {
                self.text(
                    &app.name.chars().next().unwrap_or('?').to_string(),
                    x + 70.0,
                    934.0,
                    30.0,
                    [230, 236, 245],
                );
            }
            self.text(
                &short(&app.name, 12),
                x + 10.0,
                976.0,
                17.0,
                [225, 233, 243],
            );
        }
    }
    fn search(&mut self, model: &Model, icons: &HashMap<String, Option<Pixmap>>) {
        self.text("Buscar aplicaciones", 88.0, 185.0, 43.0, [243, 246, 250]);
        self.rounded(88.0, 220.0, 760.0, 72.0, 20.0, [36, 44, 58, 255]);
        self.text(
            &format!("{}│", short(&model.query, 38)),
            110.0,
            267.0,
            29.0,
            [243, 247, 251],
        );
        for (row, letters) in KEYBOARD.iter().enumerate() {
            for (column, ch) in letters.chars().enumerate() {
                let (x, y) = (88.0 + column as f32 * 70.0, 340.0 + row as f32 * 80.0);
                let selected =
                    model.band == 1 && model.keyboard_row == row && model.index == column;
                self.rounded(
                    x,
                    y,
                    60.0,
                    64.0,
                    12.0,
                    if selected {
                        model.focus_color()
                    } else {
                        [41, 49, 64, 255]
                    },
                );
                self.text(
                    &ch.to_string(),
                    x + 17.0,
                    y + 43.0,
                    26.0,
                    if selected {
                        [18, 23, 30]
                    } else {
                        [231, 238, 248]
                    },
                );
            }
        }
        self.text(
            "Espacio · ⌫ Borrar · ✓ Ver resultados",
            90.0,
            715.0,
            24.0,
            [174, 192, 215],
        );
        let apps = model.row(2);
        let start = if model.band == 2 {
            model.index.saturating_sub(4)
        } else {
            0
        };
        self.text(
            &format!("{} resultados", apps.len()),
            970.0,
            185.0,
            31.0,
            [230, 237, 247],
        );
        for (index, app) in apps.iter().enumerate().skip(start).take(8) {
            let y = 230.0 + (index - start) as f32 * 93.0;
            let selected = model.band == 2 && model.index == index;
            self.rounded(
                970.0,
                y,
                840.0,
                79.0,
                16.0,
                if selected {
                    model.focus_color()
                } else {
                    [34, 42, 56, 255]
                },
            );
            if let Some(Some(icon)) = icons.get(&app.id) {
                self.image(icon, 989.0, y + 14.0, 48.0);
            }
            self.text(
                &short(&app.name, 42),
                1065.0,
                y + 50.0,
                29.0,
                if selected {
                    [18, 23, 30]
                } else {
                    [230, 237, 247]
                },
            );
        }
    }
    fn settings(&mut self, model: &Model) {
        self.text("Ajustes", 88.0, 185.0, 43.0, [243, 246, 250]);
        for (index, label) in SETTING_ITEMS.iter().enumerate() {
            let selected = model.band > 0 && model.index == index;
            let y = 225.0 + index as f32 * 72.0;
            self.rounded(
                88.0,
                y,
                840.0,
                60.0,
                14.0,
                if selected {
                    model.focus_color()
                } else {
                    [32, 39, 52, 255]
                },
            );
            self.text(
                label,
                111.0,
                y + 40.0,
                26.0,
                if selected {
                    [18, 23, 30]
                } else {
                    [230, 237, 247]
                },
            );
        }
        self.text("Sonido", 1080.0, 285.0, 32.0, [235, 241, 249]);
        self.text(
            &short(&model.volume, 46),
            1080.0,
            339.0,
            25.0,
            [178, 199, 221],
        );
        self.text("Red", 1080.0, 445.0, 32.0, [235, 241, 249]);
        self.text(
            &short(&model.network, 46),
            1080.0,
            499.0,
            25.0,
            [178, 199, 221],
        );
        self.text("Android", 1080.0, 605.0, 32.0, [235, 241, 249]);
        self.text(
            &short(&model.android, 46),
            1080.0,
            659.0,
            25.0,
            [178, 199, 221],
        );
        self.text(
            if model.settings.reduced_motion {
                "Movimiento reducido: activado"
            } else {
                "Movimiento reducido: desactivado"
            },
            1080.0,
            815.0,
            25.0,
            [178, 199, 221],
        );
    }
    fn context(&mut self, model: &Model) {
        self.rect(0.0, 0.0, 1920.0, 1080.0, [0, 0, 0, 190]);
        let Some((id, selected)) = &model.context else {
            return;
        };
        let title = model
            .apps
            .iter()
            .find(|app| &app.id == id)
            .map(|app| app.name.as_str())
            .unwrap_or("Aplicación");
        let labels = model.context_labels();
        let height = 145.0 + labels.len() as f32 * 75.0;
        self.rounded(560.0, 230.0, 800.0, height, 30.0, [26, 32, 43, 255]);
        self.text(&short(title, 35), 605.0, 303.0, 34.0, [240, 245, 251]);
        for (index, label) in labels.iter().enumerate() {
            let y = 340.0 + index as f32 * 75.0;
            let active = index == *selected;
            self.rounded(
                590.0,
                y,
                740.0,
                62.0,
                15.0,
                if active {
                    model.focus_color()
                } else {
                    [40, 48, 63, 255]
                },
            );
            self.text(
                label,
                615.0,
                y + 42.0,
                28.0,
                if active {
                    [18, 23, 30]
                } else {
                    [229, 237, 248]
                },
            );
        }
    }
}
