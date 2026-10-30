//! Read-only probe: never starts an Android session.
use archtv_core::android::AndroidProvider;
use std::{
    process::ExitCode,
    time::{Duration, Instant},
};
fn main() -> ExitCode {
    let mut provider = archtv_android::Waydroid::default();
    match provider.status(Instant::now() + Duration::from_secs(4)) {
        Ok(status) => {
            println!(
                "session={:?} boot={:?} boot_ready={}",
                status.session,
                status.boot,
                status.boot_ready()
            );
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!(
                "provider_error={:?} effect_applied={:?}",
                error.kind, error.effect_applied
            );
            ExitCode::FAILURE
        }
    }
}
