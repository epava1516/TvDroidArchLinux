use crate::layout::*;
use crate::{
    model::{KEYBOARD, MENU_ITEMS, Model, Page, SETTING_ITEMS},
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
        let (w, h) = if wide {
            (FEATURE_WIDTH, FEATURE_HEIGHT)
        } else {
            (322.0, 155.0)
        };
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
        if model.page == Page::Home {
            self.cached_home_background();
        } else {
            self.pixmap
                .fill(tiny_skia::Color::from_rgba8(14, 16, 22, 255));
        }
        self.header(model);
        match model.page {
            Page::Home => self.home(model, icons),
            Page::Apps | Page::Recent | Page::Linux | Page::Android => self.grid(model, icons),
            Page::Search => self.search(model, icons),
            Page::Settings => self.settings(model),
            Page::Menu => self.menu(model),
        }
        if model.page != Page::Home {
            self.rect(0.0, 1020.0, 1920.0, 60.0, [14, 16, 22, 255]);
            self.text(
                &short(&model.notice, 116),
                SAFE_LEFT,
                1059.0,
                21.0,
                [175, 191, 210],
            );
        }
        if model.context.is_some() {
            self.context(model);
        }
    }
    fn cached_home_background(&mut self) {
        if self.home_background.is_none() {
            let width = self.pixmap.width();
            let scale = self.scale();
            for (index, pixel) in self.pixmap.data_mut().chunks_exact_mut(4).enumerate() {
                let x = (index % width as usize) as f32 / width as f32;
                let y = (index / width as usize) as f32 / scale;
                let right = ((x - 0.15) / 0.85).clamp(0.0, 1.0);
                let top = (y / 145.0).clamp(0.0, 1.0);
                let bottom = ((830.0 - y) / 260.0).clamp(0.0, 1.0);
                let amount = right * top * bottom;
                for channel in 0..3 {
                    let base = [14.0, 16.0, 22.0][channel];
                    pixel[channel] = (base + amount * ([38.0, 77.0, 96.0][channel] - base)) as u8;
                }
                pixel[3] = 255;
            }
            self.rounded(1180.0, 175.0, 500.0, 300.0, 150.0, [34, 88, 105, 220]);
            self.rounded(1280.0, 200.0, 320.0, 250.0, 125.0, [48, 129, 134, 220]);
            if let Some(image) = &self.wallpaper {
                self.pixmap
                    .fill(tiny_skia::Color::from_rgba8(14, 16, 22, 255));
                let factor = self.pixmap.width() as f32 / image.width() as f32;
                self.pixmap.draw_pixmap(
                    0,
                    0,
                    image.as_ref().as_ref(),
                    &tiny_skia::PixmapPaint::default(),
                    tiny_skia::Transform::from_scale(factor, factor),
                    None,
                );
                let width = self.pixmap.width() as usize;
                for (index, pixel) in self.pixmap.data_mut().chunks_exact_mut(4).enumerate() {
                    let y = (index / width) as f32 / scale;
                    let shade = (((y - 510.0) / 320.0).clamp(0.0, 1.0))
                        .max((1.0 - y / 185.0).clamp(0.0, 1.0) * 0.55);
                    for channel in 0..3 {
                        pixel[channel] = (f32::from(pixel[channel]) * (1.0 - shade)
                            + [14.0, 16.0, 22.0][channel] * shade)
                            as u8;
                    }
                }
            }
            self.home_background = Some(self.pixmap.clone());
        }
        if let Some(background) = &self.home_background {
            self.pixmap.data_mut().copy_from_slice(background.data());
        }
    }
    fn header(&mut self, model: &Model) {
        for (index, x) in NAV_X.iter().enumerate() {
            let selected = index == model.page.index();
            if selected {
                if model.band == 0 {
                    self.rounded(
                        *x - 35.0,
                        NAV_Y - 35.0,
                        70.0,
                        70.0,
                        19.0,
                        model.focus_color(),
                    );
                }
                self.rounded(*x - 33.0, NAV_Y - 33.0, 66.0, 66.0, 18.0, [54, 54, 54, 255]);
            }
            self.nav_icon(index, *x, NAV_Y, 36.0, [233, 234, 236, 255]);
        }
        if model.band == 0 {
            let label = model.page.label();
            self.text(
                label,
                (NAV_X[model.page.index()] - label.chars().count() as f32 * 6.0).max(50.0),
                137.0,
                21.0,
                [231, 234, 240],
            );
        }
        self.text("arch tv", 1738.0, 73.0, 26.0, [243, 245, 249]);
    }
    fn nav_icon(&mut self, index: usize, x: f32, y: f32, size: f32, color: [u8; 4]) {
        use tiny_skia::{LineCap, LineJoin, Paint, PathBuilder, Rect, Stroke, Transform};
        let mut path = PathBuilder::new();
        match index {
            0 => {
                for y in [6.0, 12.0, 18.0] {
                    path.move_to(4.0, y);
                    path.line_to(20.0, y);
                }
            }
            1 => {
                path.push_circle(10.0, 10.0, 6.5);
                path.move_to(15.0, 15.0);
                path.line_to(21.0, 21.0);
            }
            2 => {
                path.move_to(2.0, 11.0);
                path.line_to(12.0, 3.0);
                path.line_to(22.0, 11.0);
                path.move_to(5.0, 9.0);
                path.line_to(5.0, 21.0);
                path.line_to(19.0, 21.0);
                path.line_to(19.0, 9.0);
                path.move_to(10.0, 21.0);
                path.line_to(10.0, 15.0);
                path.line_to(14.0, 15.0);
                path.line_to(14.0, 21.0);
            }
            3 => {
                path.push_rect(Rect::from_xywh(3.0, 4.0, 18.0, 13.0).unwrap());
                path.move_to(12.0, 17.0);
                path.line_to(12.0, 21.0);
                path.move_to(7.0, 21.0);
                path.line_to(17.0, 21.0);
            }
            4 => {
                path.push_circle(12.0, 12.0, 9.0);
                path.move_to(12.0, 6.0);
                path.line_to(12.0, 12.0);
                path.line_to(17.0, 15.0);
            }
            5 => {
                path.push_rect(Rect::from_xywh(2.0, 4.0, 20.0, 16.0).unwrap());
                path.move_to(6.0, 8.0);
                path.line_to(9.0, 11.0);
                path.line_to(6.0, 14.0);
                path.move_to(12.0, 15.0);
                path.line_to(18.0, 15.0);
            }
            6 => {
                path.push_circle(12.0, 12.0, 7.0);
                path.move_to(7.0, 6.0);
                path.line_to(5.0, 2.0);
                path.move_to(17.0, 6.0);
                path.line_to(19.0, 2.0);
                path.move_to(9.0, 11.0);
                path.line_to(9.0, 11.2);
                path.move_to(15.0, 11.0);
                path.line_to(15.0, 11.2);
                path.move_to(8.0, 19.0);
                path.line_to(8.0, 22.0);
                path.move_to(16.0, 19.0);
                path.line_to(16.0, 22.0);
            }
            _ => {
                for point in 0..32 {
                    let angle = point as f32 * std::f32::consts::TAU / 32.0;
                    let radius = if point % 4 < 2 { 10.0 } else { 8.0 };
                    let (x, y) = (12.0 + angle.cos() * radius, 12.0 + angle.sin() * radius);
                    if point == 0 {
                        path.move_to(x, y);
                    } else {
                        path.line_to(x, y);
                    }
                }
                path.close();
                path.push_circle(12.0, 12.0, 3.5);
            }
        }
        if let Some(path) = path.finish() {
            let mut paint = Paint::default();
            paint.set_color_rgba8(color[0], color[1], color[2], color[3]);
            let stroke = Stroke {
                width: 1.7,
                line_cap: LineCap::Round,
                line_join: LineJoin::Round,
                ..Stroke::default()
            };
            let scale = self.scale();
            self.pixmap.stroke_path(
                &path,
                &paint,
                &stroke,
                Transform::from_scale(size * scale / 24.0, size * scale / 24.0)
                    .post_translate((x - size / 2.0) * scale, (y - size / 2.0) * scale),
                None,
            );
        }
    }
    fn grid(&mut self, model: &Model, icons: &HashMap<String, Option<Pixmap>>) {
        let title = match model.page {
            Page::Recent => "Abiertas recientemente",
            Page::Linux => "Aplicaciones Linux",
            Page::Android => "Aplicaciones Android",
            _ => "Tus aplicaciones",
        };
        self.text(title, SAFE_LEFT, 195.0, 43.0, [244, 247, 250]);
        self.text(
            "Mantén Seleccionar o pulsa Menú para organizar",
            SAFE_LEFT,
            245.0,
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
                SAFE_LEFT,
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
                    SAFE_LEFT + (cell % 5) as f32 * 347.0,
                    295.0 + (cell / 5) as f32 * 176.0,
                ),
                false,
                model.band > 0 && model.index == position,
            );
        }
    }
    fn home(&mut self, model: &Model, icons: &HashMap<String, Option<Pixmap>>) {
        if let Some(app) = model.selected() {
            self.text(
                &short(&app.name, 23),
                SAFE_LEFT,
                300.0,
                58.0,
                [248, 249, 251],
            );
            self.text(
                &short(&app.comment, 64),
                SAFE_LEFT,
                365.0,
                25.0,
                [199, 210, 225],
            );
            self.text(
                if app.android {
                    "Aplicación Android"
                } else {
                    "Aplicación Linux instalada"
                },
                SAFE_LEFT,
                415.0,
                24.0,
                [170, 190, 208],
            );
            if let Some(Some(icon)) = icons.get(&app.id) {
                self.image(icon, 1320.0, 240.0, 180.0);
            }
        } else {
            self.text("Tu televisión.", SAFE_LEFT, 275.0, 68.0, [248, 249, 251]);
            self.text("A tu manera.", SAFE_LEFT, 355.0, 68.0, [248, 249, 251]);
            self.text(
                "Tu biblioteca de aplicaciones Linux y Android",
                SAFE_LEFT,
                415.0,
                25.0,
                [191, 204, 220],
            );
        }
        if model.band == 1 {
            self.rounded(
                SAFE_LEFT - 5.0,
                483.0,
                220.0,
                74.0,
                36.0,
                model.focus_color(),
            );
        }
        self.rounded(SAFE_LEFT, 488.0, 210.0, 64.0, 32.0, [241, 243, 247, 255]);
        self.text("Ver apps", SAFE_LEFT + 43.0, 531.0, 27.0, [20, 24, 31]);
        let row = model.row(2);
        let start = if model.band == 2 {
            model.index.saturating_sub(4)
        } else {
            0
        };
        for (index, app) in row.iter().enumerate().skip(start).take(6) {
            self.application(
                model,
                icons,
                app,
                (SAFE_LEFT + (index - start) as f32 * FEATURE_STEP, FEATURE_Y),
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
                SAFE_LEFT,
                710.0,
                30.0,
                [208, 218, 231],
            );
        }
        let row = model.row(3);
        let start = if model.band == 3 {
            model.index.saturating_sub(9)
        } else {
            0
        };
        for (index, app) in row.iter().enumerate().skip(start).take(11) {
            let x = SAFE_LEFT + (index - start) as f32 * APP_STEP;
            if model.band == 3 && model.index == index {
                self.rounded(
                    x - 5.0,
                    APP_Y - 5.0,
                    APP_WIDTH + 10.0,
                    APP_HEIGHT + 10.0,
                    20.0,
                    model.focus_color(),
                );
            }
            self.rounded(x, APP_Y, APP_WIDTH, APP_HEIGHT, 16.0, [32, 38, 49, 255]);
            if let Some(Some(icon)) = icons.get(&app.id) {
                self.image(icon, x + 51.0, APP_Y + 6.0, 48.0);
            } else {
                self.text(
                    &app.name.chars().next().unwrap_or('?').to_string(),
                    x + 62.0,
                    APP_Y + 40.0,
                    29.0,
                    [230, 236, 245],
                );
            }
            self.text(
                &short(&app.name, 12),
                x + 11.0,
                APP_Y + 73.0,
                17.0,
                [225, 233, 243],
            );
        }
        let width = 1920.0 - SAFE_LEFT * 2.0;
        if model.band == 4 {
            self.rounded(
                SAFE_LEFT - 4.0,
                BANNER_Y - 4.0,
                width + 8.0,
                BANNER_HEIGHT + 8.0,
                22.0,
                model.focus_color(),
            );
        }
        self.rounded(
            SAFE_LEFT,
            BANNER_Y,
            width,
            BANNER_HEIGHT,
            18.0,
            [27, 49, 68, 255],
        );
        self.text(
            if model.settings.recent.is_empty() {
                "Explora tus aplicaciones"
            } else {
                "Abiertas recientemente"
            },
            SAFE_LEFT + 36.0,
            BANNER_Y + 53.0,
            34.0,
            [242, 246, 251],
        );
        self.text(
            &short(&model.notice, 90),
            SAFE_LEFT + 36.0,
            BANNER_Y + 100.0,
            23.0,
            [183, 205, 226],
        );
        self.text("arch tv", 1650.0, BANNER_Y + 78.0, 33.0, [230, 239, 250]);
    }
    fn menu(&mut self, model: &Model) {
        self.text("Menú", SAFE_LEFT, 195.0, 43.0, [243, 246, 250]);
        for (index, label) in MENU_ITEMS.iter().enumerate() {
            let y = 245.0 + index as f32 * 82.0;
            let selected = model.band > 0 && model.index == index;
            self.rounded(
                SAFE_LEFT,
                y,
                900.0,
                68.0,
                16.0,
                if selected {
                    model.focus_color()
                } else {
                    [32, 39, 52, 255]
                },
            );
            self.text(
                label,
                SAFE_LEFT + 25.0,
                y + 45.0,
                28.0,
                if selected {
                    [18, 23, 30]
                } else {
                    [230, 237, 247]
                },
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
