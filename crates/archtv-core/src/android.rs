//! Draft A0 provider contract. No IPC transport or Android runtime is implemented here.
use std::{fs::File, time::Instant};

pub const CONTRACT_VERSION: u32 = 1;

/// Package identity is distinct from desktop IDs, labels and Wayland app_id.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct AppId {
    package: String,
    user: u32,
}
impl AppId {
    /// ASCII package-name subset supported by contract v1, including `android`.
    pub fn new(package: &str, user: u32) -> Result<Self, ErrorKind> {
        if package.is_empty()
            || package.len() > 255
            || !package.split('.').all(|segment| {
                let mut bytes = segment.bytes();
                bytes
                    .next()
                    .is_some_and(|first| first.is_ascii_alphabetic())
                    && bytes.all(|byte| byte.is_ascii_alphanumeric() || byte == b'_')
            })
        {
            return Err(ErrorKind::InvalidRequest);
        }
        Ok(Self {
            package: package.into(),
            user,
        })
    }
    pub fn package(&self) -> &str {
        &self.package
    }
    pub fn user(&self) -> u32 {
        self.user
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Abi {
    X86,
    X86_64,
    ArmeabiV7a,
    Arm64V8a,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Capability {
    InstallApk,
    ListApps,
    Launch,
    ForceStop,
    Suspend,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ProviderInfo {
    pub contract_version: u32,
    pub id: String,
    pub version: String,
    pub android_api: Option<u32>,
    /// ABIs executable by this provider; no implicit architecture translation.
    pub abis: Vec<Abi>,
    pub capabilities: Vec<Capability>,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum SessionState {
    Stopped,
    Starting,
    Running,
    Suspended,
    Unknown,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum BootState {
    Starting,
    Completed,
    Unknown,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct RuntimeStatus {
    pub session: SessionState,
    pub boot: BootState,
}
impl RuntimeStatus {
    /// Boot readiness alone says nothing about graphics, audio or app compatibility.
    pub fn boot_ready(&self) -> bool {
        self.session == SessionState::Running && self.boot == BootState::Completed
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum AppState {
    Stopped,
    Running,
    Unknown,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct App {
    pub id: AppId,
    pub label: String,
    pub version_code: Option<u64>,
    pub launchable: bool,
    /// Execution state is independent of window visibility or foreground focus.
    pub execution: AppState,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum InstallPolicy {
    NewOnly,
    /// Preserve app data; downgrade and uninstall are separate future operations.
    Replace,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct InstallReceipt {
    pub app: AppId,
    pub version_code: Option<u64>,
    pub replaced: bool,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LaunchReceipt {
    pub app: AppId,
    /// Provider-owned operation identifier, not a PID or a trusted surface identity.
    pub operation: String,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ErrorKind {
    Unavailable,
    NotReady,
    TimedOut,
    PermissionDenied,
    InvalidRequest,
    IncompatibleAbi,
    Unsupported,
    NotFound,
    Conflict,
    BackendFailure,
}
/// The caller owns localization; adapters must not return raw command output here.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ProviderError {
    pub kind: ErrorKind,
    /// None if the backend cannot establish whether a timed-out mutation took effect.
    pub effect_applied: Option<bool>,
}
pub type ProviderResult<T> = Result<T, ProviderError>;

/// Blocking operations run on workers, never on the compositor/UI event loop.
/// Each adapter must enforce the absolute deadline, including child cleanup.
/// This trait defines requirements, not an enforcement mechanism or IPC ABI.
pub trait AndroidProvider: Send {
    fn info(&self) -> ProviderInfo;
    fn status(&mut self, deadline: Instant) -> ProviderResult<RuntimeStatus>;
    fn start_runtime(&mut self, deadline: Instant) -> ProviderResult<()>;
    fn stop_runtime(&mut self, deadline: Instant) -> ProviderResult<()>;
    fn list_apps(&mut self, user: u32, deadline: Instant) -> ProviderResult<Vec<App>>;
    fn app_status(&mut self, app: &AppId, deadline: Instant) -> ProviderResult<AppState>;
    /// Borrow a pre-opened read-only APK; never interpret a path as a shell command.
    /// User selects an Android profile, not an authorization grant.
    fn install_apk(
        &mut self,
        apk: &File,
        user: u32,
        policy: InstallPolicy,
        deadline: Instant,
    ) -> ProviderResult<InstallReceipt>;
    /// Acceptance does not imply that a surface appeared or a frame was presented.
    fn launch(&mut self, app: &AppId, deadline: Instant) -> ProviderResult<LaunchReceipt>;
    /// Stop this app's execution without uninstalling it or deleting its data.
    fn force_stop(&mut self, app: &AppId, deadline: Instant) -> ProviderResult<()>;
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn identity_rejects_commands_and_keeps_android_profiles_distinct() {
        for value in [
            "",
            "-x",
            "com..app",
            "com.app;reboot",
            "com/app",
            "com.app\n",
            "1app",
        ] {
            assert_eq!(AppId::new(value, 0), Err(ErrorKind::InvalidRequest));
        }
        assert!(AppId::new("android", 0).is_ok());
        let owner = AppId::new("org.example.tv_app", 0).unwrap();
        let profile = AppId::new("org.example.tv_app", 10).unwrap();
        assert_ne!(owner, profile);
        assert_eq!(owner.package(), "org.example.tv_app");
        assert_eq!(profile.user(), 10);
    }

    #[test]
    fn stale_boot_confirmation_cannot_make_a_stopped_session_ready() {
        for session in [
            SessionState::Stopped,
            SessionState::Starting,
            SessionState::Suspended,
            SessionState::Unknown,
        ] {
            assert!(
                !RuntimeStatus {
                    session,
                    boot: BootState::Completed
                }
                .boot_ready()
            );
        }
        for boot in [BootState::Unknown, BootState::Starting] {
            assert!(
                !RuntimeStatus {
                    session: SessionState::Running,
                    boot
                }
                .boot_ready()
            );
        }
        assert!(
            RuntimeStatus {
                session: SessionState::Running,
                boot: BootState::Completed
            }
            .boot_ready()
        );
    }
}
