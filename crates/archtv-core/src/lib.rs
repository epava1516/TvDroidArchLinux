//! TV session policy independent from Wayland, rendering and application toolkits.

/// Most-recently-focused applications and an optional persistent home surface.
#[derive(Debug)]
pub struct FocusStack<T> {
    history: Vec<T>,
    home: Option<T>,
}
impl<T> Default for FocusStack<T> {
    fn default() -> Self {
        Self {
            history: Vec::new(),
            home: None,
        }
    }
}
impl<T: Clone + Eq> FocusStack<T> {
    pub fn activate(&mut self, item: T) {
        self.history.retain(|old| old != &item);
        self.history.push(item);
    }
    pub fn set_home(&mut self, item: T) {
        self.home = Some(item.clone());
        self.activate(item);
    }
    pub fn home(&mut self) -> Option<T> {
        let home = self.home.clone()?;
        self.activate(home.clone());
        Some(home)
    }
    pub fn remove(&mut self, item: &T) -> Option<T> {
        self.history.retain(|old| old != item);
        if self.home.as_ref() == Some(item) {
            self.home = None;
        }
        self.current().cloned()
    }
    pub fn current(&self) -> Option<&T> {
        self.history.last()
    }
    pub fn previous(&mut self) -> Option<T> {
        if self.history.len() > 1 {
            let current = self.history.pop().unwrap();
            self.history.insert(0, current);
        }
        self.current().cloned()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn home_returns_without_destroying_app_and_close_restores_focus() {
        let mut stack = FocusStack::default();
        stack.set_home("shell");
        stack.activate("android");
        assert_eq!(stack.home(), Some("shell"));
        assert_eq!(stack.previous(), Some("android"));
        assert_eq!(stack.remove(&"android"), Some("shell"));
        assert_eq!(stack.remove(&"shell"), None);
        assert_eq!(stack.home(), None);
    }
    #[test]
    fn repeated_activation_does_not_duplicate_a_window() {
        let mut stack = FocusStack::default();
        stack.activate(1);
        stack.activate(2);
        stack.activate(2);
        assert_eq!(stack.remove(&2), Some(1));
        assert_eq!(stack.remove(&1), None);
    }
}

pub mod desktop;

pub mod android;

#[cfg(target_os = "linux")]
pub mod native_process;
