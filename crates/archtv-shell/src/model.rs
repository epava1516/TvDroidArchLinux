use archtv_core::desktop::Application;
use serde::{Deserialize, Serialize};
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(default)]
pub struct Settings {
    pub version: u32,
    pub favorites: Vec<String>,
    pub recent: Vec<String>,
    pub hidden: Vec<String>,
    pub reduced_motion: bool,
}
impl Default for Settings {
    fn default() -> Self {
        Self {
            version: 1,
            favorites: vec![],
            recent: vec![],
            hidden: vec![],
            reduced_motion: true,
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Page {
    Search,
    Home,
    Apps,
    Recent,
    Settings,
}
impl Page {
    pub fn index(self) -> usize {
        match self {
            Self::Search => 0,
            Self::Home => 1,
            Self::Apps => 2,
            Self::Recent => 3,
            Self::Settings => 4,
        }
    }
    pub fn from_index(index: usize) -> Self {
        [
            Self::Search,
            Self::Home,
            Self::Apps,
            Self::Recent,
            Self::Settings,
        ][index.min(4)]
    }
}
#[derive(Clone, Debug)]
pub enum Action {
    Launch(Application),
    Save(Settings),
    Volume(i8),
    Mute,
    Wifi,
    Refresh,
    AndroidStart,
    AndroidStop,
    Quit,
    Resume,
}
#[derive(Clone, Copy, Debug)]
pub enum Key {
    Left,
    Right,
    Up,
    Down,
    Enter,
    Back,
    Menu,
    Backspace,
    Character(char),
}
#[derive(Clone, Copy, Debug)]
pub enum ContextAction {
    Favorite,
    Left,
    Right,
    Hide,
    Cancel,
}
pub const KEYBOARD: [&str; 4] = ["QWERTYUIOP", "ASDFGHJKLÑ", "ZXCVBNM", " ⌫✓"];
pub const SETTING_ITEMS: [&str; 10] = [
    "Bajar volumen",
    "Subir volumen",
    "Silenciar / activar sonido",
    "Activar / desactivar Wi-Fi",
    "Actualizar estado",
    "Restaurar aplicaciones ocultas",
    "Movimiento reducido",
    "Iniciar sesión Android",
    "Detener sesión Android",
    "Cerrar sesión",
];
pub struct Model {
    pub focus_glow: u8,
    pub apps: Vec<Application>,
    pub settings: Settings,
    pub page: Page,
    pub band: u8,
    pub index: usize,
    pub memory: [usize; 4],
    pub query: String,
    pub keyboard_row: usize,
    pub context: Option<(String, usize)>,
    pub notice: String,
    pub volume: String,
    pub network: String,
    pub android: String,
    pub loading: bool,
}
impl Default for Model {
    fn default() -> Self {
        Self {
            focus_glow: 255,
            apps: vec![],
            settings: Settings::default(),
            page: Page::Home,
            band: 2,
            index: 0,
            memory: [0; 4],
            query: String::new(),
            keyboard_row: 0,
            context: None,
            notice: "Preparando tus aplicaciones…".into(),
            volume: "Consultando…".into(),
            network: "Consultando…".into(),
            android: "Consultando…".into(),
            loading: true,
        }
    }
}
impl Model {
    pub fn focus_color(&self) -> [u8; 4] {
        [245, 247, 250, self.focus_glow]
    }
    pub fn visible(&self) -> Vec<&Application> {
        self.apps
            .iter()
            .filter(|app| !self.settings.hidden.contains(&app.id))
            .collect()
    }
    pub fn row(&self, band: u8) -> Vec<&Application> {
        let visible = self.visible();
        let ordered = |ids: &Vec<String>| {
            ids.iter()
                .filter_map(|id| visible.iter().find(|app| &app.id == id).copied())
                .collect::<Vec<_>>()
        };
        match self.page {
            Page::Home if band == 2 => {
                let favorites = ordered(&self.settings.favorites);
                if favorites.is_empty() {
                    visible.iter().copied().take(12).collect()
                } else {
                    favorites
                }
            }
            Page::Recent => ordered(&self.settings.recent),
            Page::Search => {
                let query = self.query.to_lowercase();
                visible
                    .into_iter()
                    .filter(|app| {
                        query.is_empty()
                            || app.name.to_lowercase().contains(&query)
                            || app.comment.to_lowercase().contains(&query)
                    })
                    .collect()
            }
            _ => visible,
        }
    }
    pub fn selected(&self) -> Option<&Application> {
        if self.band == 0
            || self.page == Page::Settings
            || (self.page == Page::Home && self.band == 1)
            || (self.page == Page::Search && self.band == 1)
        {
            None
        } else {
            self.row(self.band).get(self.index).copied()
        }
    }
    pub fn context_actions(&self) -> Vec<ContextAction> {
        let mut items = vec![ContextAction::Favorite];
        if self
            .context
            .as_ref()
            .is_some_and(|(id, _)| self.settings.favorites.contains(id))
        {
            items.extend([ContextAction::Left, ContextAction::Right]);
        }
        items.extend([ContextAction::Hide, ContextAction::Cancel]);
        items
    }
    pub fn context_labels(&self) -> Vec<String> {
        self.context_actions()
            .iter()
            .map(|item| {
                match item {
                    ContextAction::Favorite => {
                        if self
                            .context
                            .as_ref()
                            .is_some_and(|(id, _)| self.settings.favorites.contains(id))
                        {
                            "Quitar de favoritos"
                        } else {
                            "Añadir a favoritos"
                        }
                    }
                    ContextAction::Left => "Mover a la izquierda",
                    ContextAction::Right => "Mover a la derecha",
                    ContextAction::Hide => "Ocultar aplicación",
                    ContextAction::Cancel => "Cancelar",
                }
                .into()
            })
            .collect()
    }
    pub fn clamp(&mut self) {
        if self.band == 0 {
            self.index = self.page.index();
            return;
        }
        if self.page == Page::Settings {
            self.index = self.index.min(SETTING_ITEMS.len() - 1);
        } else if self.page == Page::Search && self.band == 1 {
            self.index = self
                .index
                .min(KEYBOARD[self.keyboard_row].chars().count() - 1);
        } else {
            self.index = self.index.min(self.row(self.band).len().saturating_sub(1));
        }
    }
    pub fn show_context(&mut self) {
        if let Some(app) = self.selected() {
            self.context = Some((app.id.clone(), 0));
        }
    }
    pub fn launched(&mut self, id: String) {
        self.settings.recent.retain(|old| old != &id);
        self.settings.recent.insert(0, id);
        self.settings.recent.truncate(20);
    }
    pub fn key(&mut self, key: Key) -> Vec<Action> {
        if self.context.is_some() {
            return self.context_key(key);
        }
        if matches!(key, Key::Menu) {
            self.show_context();
            return vec![];
        }
        if matches!(key, Key::Back) {
            if self.band == 0 && self.page == Page::Home {
                return vec![Action::Resume];
            }
            self.page = Page::Home;
            self.band = 0;
            self.index = 1;
            return vec![];
        }
        if let Key::Character(ch) = key {
            if !ch.is_control() {
                self.page = Page::Search;
                self.band = 1;
                if self.query.chars().count() < 80 {
                    self.query.push(ch);
                }
                self.index = 0;
            }
            return vec![];
        }
        if matches!(key, Key::Backspace) {
            if self.page == Page::Search {
                self.query.pop();
            }
            return vec![];
        }
        if self.band == 0 {
            match key {
                Key::Left => self.index = self.index.saturating_sub(1),
                Key::Right => self.index = (self.index + 1).min(4),
                Key::Down | Key::Enter => {
                    self.band = 1;
                    self.index = self.memory[self.band as usize];
                    self.clamp();
                    return vec![];
                }
                _ => (),
            }
            self.page = Page::from_index(self.index);
            return vec![];
        }
        if self.page == Page::Settings {
            match key {
                Key::Up if self.index == 0 => {
                    self.band = 0;
                    self.index = 4;
                }
                Key::Up => self.index -= 1,
                Key::Down => self.index = (self.index + 1).min(SETTING_ITEMS.len() - 1),
                Key::Enter => return self.setting_action(),
                _ => (),
            }
            return vec![];
        }
        if self.page == Page::Search && self.band == 1 {
            match key {
                Key::Left => self.index = self.index.saturating_sub(1),
                Key::Right if self.index + 1 >= KEYBOARD[self.keyboard_row].chars().count() => {
                    self.band = 2;
                    self.index = 0;
                }
                Key::Right => self.index += 1,
                Key::Up if self.keyboard_row == 0 => {
                    self.band = 0;
                    self.index = 0;
                }
                Key::Up => self.keyboard_row -= 1,
                Key::Down => self.keyboard_row = (self.keyboard_row + 1).min(3),
                Key::Enter => {
                    match KEYBOARD[self.keyboard_row]
                        .chars()
                        .nth(self.index)
                        .unwrap_or('✓')
                    {
                        '⌫' => {
                            self.query.pop();
                        }
                        '✓' => {
                            self.band = 2;
                            self.index = 0;
                        }
                        ch => {
                            if self.query.chars().count() < 80 {
                                self.query.push(ch.to_lowercase().next().unwrap_or(ch));
                            }
                        }
                    }
                }
                _ => (),
            }
            self.clamp();
            return vec![];
        }
        let count = self.row(self.band).len();
        match key {
            Key::Left => {
                if self.page == Page::Search && self.index == 0 {
                    self.band = 1;
                    self.index = 0;
                } else {
                    self.index = self.index.saturating_sub(1);
                }
            }
            Key::Right => self.index = (self.index + 1).min(count.saturating_sub(1)),
            Key::Up => {
                if self.page == Page::Home {
                    self.memory[self.band as usize] = self.index;
                    self.band -= 1;
                    self.index = if self.band == 0 {
                        self.page.index()
                    } else {
                        self.memory[self.band as usize]
                    };
                } else if self.index >= 5 && self.page != Page::Search {
                    self.index -= 5;
                } else {
                    self.band = 0;
                    self.index = self.page.index();
                }
            }
            Key::Down => {
                if self.page == Page::Home {
                    self.memory[self.band as usize] = self.index;
                    self.band = (self.band + 1).min(3);
                    self.index = self.memory[self.band as usize];
                } else if self.page == Page::Search {
                    self.index = (self.index + 1).min(count.saturating_sub(1));
                } else {
                    self.index = (self.index + 5).min(count.saturating_sub(1));
                }
            }
            Key::Enter => {
                if self.page == Page::Home && self.band == 1 {
                    self.page = Page::Apps;
                    self.band = 1;
                    self.index = 0;
                } else if let Some(app) = self.selected() {
                    return vec![Action::Launch(app.clone())];
                }
            }
            _ => (),
        }
        self.clamp();
        vec![]
    }
    fn setting_action(&mut self) -> Vec<Action> {
        if self.loading && matches!(self.index, 5 | 6) {
            return vec![];
        }
        match self.index {
            0 => vec![Action::Volume(-5)],
            1 => vec![Action::Volume(5)],
            2 => vec![Action::Mute],
            3 => vec![Action::Wifi],
            4 => vec![Action::Refresh],
            5 => {
                self.settings.hidden.clear();
                self.notice = "Aplicaciones restauradas".into();
                vec![Action::Save(self.settings.clone())]
            }
            6 => {
                self.settings.reduced_motion = !self.settings.reduced_motion;
                vec![Action::Save(self.settings.clone())]
            }
            7 => vec![Action::AndroidStart],
            8 => vec![Action::AndroidStop],
            9 => vec![Action::Quit],
            _ => vec![],
        }
    }
    fn context_key(&mut self, key: Key) -> Vec<Action> {
        let items = self.context_actions();
        let Some((id, index)) = self.context.as_mut() else {
            return vec![];
        };
        match key {
            Key::Up => *index = index.saturating_sub(1),
            Key::Down => *index = (*index + 1).min(items.len() - 1),
            Key::Back | Key::Menu => self.context = None,
            Key::Enter => {
                let id = id.clone();
                let action = items[*index];
                match action {
                    ContextAction::Favorite => {
                        if self.settings.favorites.contains(&id) {
                            self.settings.favorites.retain(|old| old != &id);
                        } else {
                            self.settings.favorites.push(id.clone());
                        }
                    }
                    ContextAction::Left | ContextAction::Right => {
                        if let Some(pos) = self.settings.favorites.iter().position(|old| old == &id)
                        {
                            let next = if matches!(action, ContextAction::Left) {
                                pos.saturating_sub(1)
                            } else {
                                (pos + 1).min(self.settings.favorites.len() - 1)
                            };
                            self.settings.favorites.swap(pos, next);
                        }
                    }
                    ContextAction::Hide => {
                        if !self.settings.hidden.contains(&id) {
                            self.settings.hidden.push(id.clone());
                        }
                    }
                    ContextAction::Cancel => (),
                }
                self.context = None;
                if let Some(position) = self.row(self.band).iter().position(|app| app.id == id) {
                    self.index = position;
                }
                self.clamp();
                return vec![Action::Save(self.settings.clone())];
            }
            _ => (),
        }
        vec![]
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    fn app(id: &str) -> Application {
        Application {
            id: id.into(),
            name: id.into(),
            comment: String::new(),
            icon: String::new(),
            command: vec![id.into()],
            directory: None,
            terminal: false,
            android: false,
        }
    }
    #[test]
    fn context_order_hide_restore_and_row_focus_survive_navigation() {
        let mut m = Model {
            apps: vec![app("one"), app("two"), app("three")],
            loading: false,
            ..Model::default()
        };
        m.key(Key::Right);
        assert_eq!(m.selected().unwrap().id, "two");
        m.show_context();
        m.key(Key::Enter);
        assert_eq!(m.settings.favorites, ["two"]);
        m.index = 0;
        m.key(Key::Down);
        m.key(Key::Right);
        m.key(Key::Right);
        m.key(Key::Up);
        assert_eq!(m.index, 0);
        m.show_context();
        m.key(Key::Down);
        m.key(Key::Down);
        m.key(Key::Down);
        m.key(Key::Enter);
        assert!(m.settings.hidden.contains(&"two".into()));
        m.page = Page::Settings;
        m.band = 1;
        m.index = 5;
        m.key(Key::Enter);
        assert!(m.settings.hidden.is_empty());
    }
    #[test]
    fn keyboard_and_physical_search_agree_and_back_is_bounded() {
        let mut m = Model {
            apps: vec![app("uno"), app("dos")],
            ..Model::default()
        };
        m.key(Key::Character('ñ'));
        assert_eq!(m.page, Page::Search);
        assert_eq!(m.query, "ñ");
        m.key(Key::Backspace);
        m.key(Key::Character('u'));
        assert_eq!(m.row(2).len(), 1);
        m.key(Key::Back);
        assert_eq!(m.page, Page::Home);
        assert_eq!(m.band, 0);
    }
}
