//! Real Binder client for the complete original Keystore2/KeyMint services.
//! This scoped integration check does not accept APK, hardware or MAC compatibility.
use android_hardware_security_keymint::aidl::android::hardware::security::keymint::{
    Algorithm::Algorithm, BlockMode::BlockMode, ErrorCode::ErrorCode,
    IKeyMintDevice::IKeyMintDevice, KeyParameter::KeyParameter,
    KeyParameterValue::KeyParameterValue as Value, KeyPurpose::KeyPurpose,
    SecurityLevel::SecurityLevel, PaddingMode::PaddingMode, Tag::Tag,
};
use android_system_keystore2::aidl::android::system::keystore2::{
    Domain::Domain, ResponseCode::ResponseCode, IKeystoreService::IKeystoreService,
    IKeystoreSecurityLevel::IKeystoreSecurityLevel, KeyDescriptor::KeyDescriptor,
};
use anyhow::{ensure, Context, Result};
use binder::Strong;
use std::{fs::OpenOptions, io::Write, os::unix::fs::OpenOptionsExt, time::{Duration, Instant}};

const SERVICE: &str = "android.system.keystore2.IKeystoreService/default";
const MESSAGE: &[u8] = b"original Keystore2 Binder persisted key";
fn param(tag: Tag, value: Value) -> KeyParameter { KeyParameter { tag, value } }
fn descriptor() -> KeyDescriptor {
    KeyDescriptor { domain: Domain::APP, nspace: -1,
        alias: Some("archtv-original-binder-aes".into()), blob: None }
}
fn operation_params(purpose: KeyPurpose, nonce: Option<&[u8]>) -> Vec<KeyParameter> {
    let mut p = vec![param(Tag::PURPOSE, Value::KeyPurpose(purpose)),
        param(Tag::BLOCK_MODE, Value::BlockMode(BlockMode::GCM)),
        param(Tag::PADDING, Value::PaddingMode(PaddingMode::NONE)),
        param(Tag::MAC_LENGTH, Value::Integer(128))];
    if let Some(nonce) = nonce { p.push(param(Tag::NONCE, Value::Blob(nonce.to_vec()))); }
    p
}
fn decrypt(level: &Strong<dyn IKeystoreSecurityLevel>, data: &[u8]) -> binder::Result<Option<Vec<u8>>> {
    let response = level.createOperation(&descriptor(),
        &operation_params(KeyPurpose::DECRYPT, Some(&data[..12])), false)?;
    response.iOperation.expect("original operation absent").finish(Some(&data[12..]), None)
}
fn main() -> Result<()> {
    let args: Vec<_> = std::env::args().collect();
    ensure!(args.len() == 3, "usage: write|read ciphertext-file");
    let provider_deadline = Instant::now() + Duration::from_secs(30);
    let keymint: Strong<dyn IKeyMintDevice> = loop {
        match binder::check_interface("android.hardware.security.keymint.IKeyMintDevice/software") {
            Ok(device) => break device,
            Err(binder::StatusCode::NAME_NOT_FOUND) => {},
            Err(error) => return Err(error.into()),
        }
        ensure!(Instant::now() < provider_deadline, "KeyMint not registered before deadline");
        std::thread::sleep(Duration::from_millis(100));
    };
    let info = keymint.getHardwareInfo()?;
    ensure!(info.securityLevel == SecurityLevel::SOFTWARE && keymint.getInterfaceVersion()? == 4,
        "provider did not report actual SOFTWARE/v4");
    if args[1] == "provider" {
        println!("KEYMINT_BINDER_SOFTWARE_V4_OBSERVED pid={} NOT_KEY_OR_APK_ACCEPTANCE", std::process::id());
        return Ok(());
    }
    let deadline = Instant::now() + Duration::from_secs(30);
    let service: Strong<dyn IKeystoreService> = loop {
        match binder::check_interface(SERVICE) {
            Ok(service) => break service,
            Err(binder::StatusCode::NAME_NOT_FOUND) => {},
            Err(error) => return Err(error.into()),
        }
        ensure!(Instant::now() < deadline, "Keystore2 not registered before deadline");
        std::thread::sleep(Duration::from_millis(100));
    };
    let level = service.getSecurityLevel(SecurityLevel::SOFTWARE)?;
    for requested in [SecurityLevel::TRUSTED_ENVIRONMENT, SecurityLevel::STRONGBOX] {
        let error = match service.getSecurityLevel(requested) {
            Ok(_) => anyhow::bail!("unavailable hardware level accepted: {requested:?}"),
            Err(error) => error,
        };
        ensure!(error.service_specific_error() == ErrorCode::HARDWARE_TYPE_UNAVAILABLE.0,
            "unexpected hardware failure: {error:?}");
    }
    if args[1] == "write" {
        let params = vec![param(Tag::ALGORITHM, Value::Algorithm(Algorithm::AES)),
            param(Tag::KEY_SIZE, Value::Integer(256)),
            param(Tag::PURPOSE, Value::KeyPurpose(KeyPurpose::ENCRYPT)),
            param(Tag::PURPOSE, Value::KeyPurpose(KeyPurpose::DECRYPT)),
            param(Tag::BLOCK_MODE, Value::BlockMode(BlockMode::GCM)),
        param(Tag::PADDING, Value::PaddingMode(PaddingMode::NONE)),
            param(Tag::MIN_MAC_LENGTH, Value::Integer(128)),
            param(Tag::NO_AUTH_REQUIRED, Value::BoolValue(true))];
        let metadata = level.generateKey(&descriptor(), None, &params, 0, &[])?;
        ensure!(metadata.keySecurityLevel == SecurityLevel::SOFTWARE, "incorrect key metadata");
        let response = level.createOperation(&descriptor(), &operation_params(KeyPurpose::ENCRYPT, None), false)?;
        let nonce = response.parameters.context("original output parameters absent")?.keyParameter.into_iter()
            .find_map(|p| match (p.tag, p.value) { (Tag::NONCE, Value::Blob(v)) => Some(v), _ => None })
            .context("original nonce absent")?;
        ensure!(nonce.len() == 12, "unexpected nonce size");
        let ciphertext = response.iOperation.context("original operation absent")?
            .finish(Some(MESSAGE), None)?.context("original ciphertext absent")?;
        let mut file = OpenOptions::new().write(true).create_new(true).mode(0o600).open(&args[2])?;
        file.write_all(&nonce)?; file.write_all(&ciphertext)?; file.sync_all()?;
        println!("KEYSTORE_BINDER_GENERATED_ENCRYPTED metadata=SOFTWARE hardware_rejected=2 pid={} NOT_APK_OR_MAC_ACCEPTANCE", std::process::id());
    } else {
        ensure!(args[1] == "read", "unknown operation");
        let entry = service.getKeyEntry(&descriptor())?;
        ensure!(entry.metadata.keySecurityLevel == SecurityLevel::SOFTWARE, "incorrect reopened metadata");
        let data = std::fs::read(&args[2])?;
        ensure!(data.len() > 28 && data.len() < 4096, "invalid captured ciphertext size");
        ensure!(decrypt(&level, &data)?.as_deref() == Some(MESSAGE), "reopened plaintext mismatch");
        let mut tampered = data; *tampered.last_mut().unwrap() ^= 1;
        let error = match decrypt(&level, &tampered) {
            Ok(_) => anyhow::bail!("tampered authenticated ciphertext accepted"), Err(error) => error,
        };
        ensure!(error.service_specific_error() == ErrorCode::VERIFICATION_FAILED.0,
            "unexpected tamper failure: {error:?}");
        service.deleteKey(&descriptor())?;
        let error = match service.getKeyEntry(&descriptor()) {
            Ok(_) => anyhow::bail!("deleted key still available"), Err(error) => error,
        };
        ensure!(error.service_specific_error() == ResponseCode::KEY_NOT_FOUND.0,
            "unexpected deleted-key failure: {error:?}");
        println!("KEYSTORE_BINDER_REOPENED_DECRYPTED tamper_rejected=1 deleted=1 metadata=SOFTWARE pid={} NOT_APK_OR_MAC_ACCEPTANCE", std::process::id());
    }
    Ok(())
}
