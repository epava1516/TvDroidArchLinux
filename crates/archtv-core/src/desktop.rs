//! Desktop entry discovery and Exec expansion without a shell interpreter.
use std::{
    collections::{BTreeMap, HashSet},
    path::{Path, PathBuf},
};
#[derive(Clone, Debug)]
pub struct Application {
    pub id: String,
    pub name: String,
    pub comment: String,
    pub icon: String,
    pub command: Vec<String>,
    pub directory: Option<PathBuf>,
    pub terminal: bool,
    pub android: bool,
}
pub fn data_directories() -> Vec<PathBuf> {
    let home = std::env::var_os("XDG_DATA_HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            PathBuf::from(std::env::var_os("HOME").unwrap_or_default()).join(".local/share")
        });
    let mut dirs = vec![home];
    dirs.extend(std::env::split_paths(
        &std::env::var_os("XDG_DATA_DIRS").unwrap_or_else(|| "/usr/local/share:/usr/share".into()),
    ));
    dirs
}
pub fn discover(directories: &[PathBuf], locale: &str) -> Vec<Application> {
    let mut entries = BTreeMap::new();
    for dir in directories {
        collect(&dir.join("applications"), "", &mut entries, 0);
    }
    let mut apps: Vec<_> = entries
        .into_iter()
        .filter_map(|(id, path)| {
            let metadata = std::fs::metadata(&path).ok()?;
            if metadata.len() > 256 * 1024 {
                return None;
            }
            let text = std::fs::read_to_string(&path).ok()?;
            parse_entry(&id, &path, &text, locale).ok().flatten()
        })
        .collect();
    apps.sort_by_key(|app| app.name.to_lowercase());
    apps.truncate(512);
    apps
}
fn collect(dir: &Path, prefix: &str, entries: &mut BTreeMap<String, PathBuf>, depth: usize) {
    if depth > 4 || entries.len() > 2048 {
        return;
    }
    let Ok(files) = std::fs::read_dir(dir) else {
        return;
    };
    let mut files: Vec<_> = files.flatten().take(4096).collect();
    files.sort_by_key(|entry| entry.file_name());
    for file in files {
        if entries.len() >= 2048 {
            break;
        }
        let path = file.path();
        let name = file.file_name().to_string_lossy().into_owned();
        let id = format!("{prefix}{name}");
        if path.is_dir() {
            collect(&path, &format!("{id}-"), entries, depth + 1);
        } else if name.ends_with(".desktop") {
            entries.entry(id).or_insert(path);
        }
    }
}
pub fn parse_entry(
    id: &str,
    path: &Path,
    text: &str,
    locale: &str,
) -> Result<Option<Application>, String> {
    let mut fields = BTreeMap::new();
    let mut active = false;
    for line in text.lines() {
        let line = line.trim();
        if line.starts_with('[') {
            active = line == "[Desktop Entry]";
            continue;
        }
        if active && !line.starts_with('#') {
            if let Some((key, value)) = line.split_once('=') {
                fields.insert(key.trim(), value.trim());
            }
        }
    }
    if fields.get("Hidden") == Some(&"true")
        || fields.get("NoDisplay") == Some(&"true")
        || fields.get("Type") != Some(&"Application")
    {
        return Ok(None);
    }
    let desktops: HashSet<_> = std::env::var("XDG_CURRENT_DESKTOP")
        .unwrap_or_else(|_| "ArchTV".into())
        .split(':')
        .map(str::to_string)
        .collect();
    if fields
        .get("OnlyShowIn")
        .is_some_and(|value| !value.split(';').any(|desktop| desktops.contains(desktop)))
        || fields
            .get("NotShowIn")
            .is_some_and(|value| value.split(';').any(|desktop| desktops.contains(desktop)))
    {
        return Ok(None);
    }
    if let Some(binary) = fields.get("TryExec") {
        if !executable(binary) {
            return Ok(None);
        }
    }
    let language = locale.split(['_', '.', '@']).next().unwrap_or("en");
    let locale = locale.split('.').next().unwrap_or(locale);
    let localized = |key: &str| {
        fields
            .get(format!("{key}[{locale}]").as_str())
            .or_else(|| fields.get(format!("{key}[{language}]").as_str()))
            .or_else(|| fields.get(key))
            .copied()
            .unwrap_or("")
            .to_string()
    };
    if id.len() > 512 {
        return Ok(None);
    }
    let name: String = unescape(&localized("Name")).chars().take(128).collect();
    if name.is_empty() {
        return Ok(None);
    }
    let icon = fields.get("Icon").copied().unwrap_or("").to_string();
    let command = expand_exec(
        fields.get("Exec").ok_or("desktop entry has no Exec")?,
        &name,
        &icon,
        path,
    )?;
    if command.is_empty() {
        return Err("empty Exec".into());
    }
    Ok(Some(Application {
        id: id.into(),
        name,
        comment: unescape(&localized("Comment")).chars().take(512).collect(),
        icon,
        command,
        directory: fields
            .get("Path")
            .filter(|value| !value.is_empty())
            .map(PathBuf::from),
        terminal: fields.get("Terminal") == Some(&"true"),
        android: id.starts_with("waydroid.") || text.contains("X-WayDroid"),
    }))
}
fn unescape(value: &str) -> String {
    let mut result = String::new();
    let mut chars = value.chars();
    while let Some(ch) = chars.next() {
        if ch == '\\' {
            result.push(match chars.next() {
                Some('s') => ' ',
                Some('n') => ' ',
                Some('t') => ' ',
                Some(other) => other,
                None => '\\',
            });
        } else {
            result.push(ch);
        }
    }
    result
}
pub fn executable(program: &str) -> bool {
    use std::os::unix::fs::PermissionsExt;
    let check = |path: PathBuf| {
        std::fs::metadata(path)
            .is_ok_and(|meta| meta.is_file() && meta.permissions().mode() & 0o111 != 0)
    };
    if program.contains('/') {
        return check(PathBuf::from(program));
    }
    std::env::split_paths(&std::env::var_os("PATH").unwrap_or_default())
        .any(|dir| check(dir.join(program)))
}
pub fn expand_exec(exec: &str, name: &str, icon: &str, path: &Path) -> Result<Vec<String>, String> {
    let mut words = Vec::new();
    let mut word = String::new();
    let mut quoted = false;
    let mut started = false;
    let mut chars = exec.chars();
    while let Some(ch) = chars.next() {
        match ch {
            '"' => {
                quoted = !quoted;
                started = true;
            }
            '\\' => {
                let next = chars.next().ok_or("trailing escape")?;
                word.push(next);
                started = true;
            }
            ch if ch.is_whitespace() && !quoted => {
                if started {
                    words.push(std::mem::take(&mut word));
                    started = false;
                }
            }
            _ => {
                word.push(ch);
                started = true;
            }
        }
    }
    if quoted {
        return Err("unterminated quoted Exec".into());
    }
    if started {
        words.push(word);
    }
    let mut result = Vec::new();
    for word in words {
        match word.as_str() {
            "%f" | "%F" | "%u" | "%U" => continue,
            "%i" => {
                if !icon.is_empty() {
                    result.extend(["--icon".into(), icon.into()]);
                }
                continue;
            }
            "%c" => {
                result.push(name.into());
                continue;
            }
            "%k" => {
                result.push(path.to_string_lossy().into_owned());
                continue;
            }
            _ => (),
        }
        let mut expanded = String::new();
        let mut chars = word.chars();
        while let Some(ch) = chars.next() {
            if ch == '%' {
                match chars.next() {
                    Some('%') => expanded.push('%'),
                    _ => return Err("unsupported or embedded Exec field code".into()),
                }
            } else {
                expanded.push(ch);
            }
        }
        result.push(expanded);
    }
    Ok(result)
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn exec_keeps_arguments_and_shell_metacharacters_literal() {
        let args = expand_exec(
            "program \"two words\" $(touch /tmp/no) %% %c %i %F",
            "Una app",
            "icon",
            Path::new("/x.desktop"),
        )
        .unwrap();
        assert_eq!(
            args,
            [
                "program",
                "two words",
                "$(touch",
                "/tmp/no)",
                "%",
                "Una app",
                "--icon",
                "icon"
            ]
        );
        assert!(expand_exec("app \"broken", "", "", Path::new("x")).is_err());
        assert!(expand_exec("app --file=%F", "", "", Path::new("x")).is_err());
    }
    #[test]
    fn locale_hidden_and_desktop_sections_are_respected() {
        let entry = "[Desktop Entry]\nType=Application\nName=English\nName[es]=Español\nExec=app %c\n[Desktop Action Other]\nName=Wrong\n";
        let app = parse_entry(
            "app.desktop",
            Path::new("/app.desktop"),
            entry,
            "es_ES.UTF-8",
        )
        .unwrap()
        .unwrap();
        assert_eq!(app.name, "Español");
        assert_eq!(app.command, ["app", "Español"]);
        assert!(
            parse_entry(
                "app",
                Path::new("x"),
                &format!("[Desktop Entry]\nHidden=true\n{entry}"),
                "en"
            )
            .unwrap()
            .is_none()
        );
    }
}
