// Linux registration glue; cryptography and the complete KeyMint v4 interface
// come from the pinned original AOSP AndroidKeyMintDevice implementation.
// This process provides SOFTWARE protection, never TEE or StrongBox.
#include <AndroidKeyMintDevice.h>
#include <android/binder_manager.h>
#include <android/binder_process.h>
#include <cstdio>

int main() {
    namespace km = aidl::android::hardware::security::keymint;
    ABinderProcess_setThreadPoolMaxThreadCount(4);
    auto device = km::CreateKeyMintDevice(km::SecurityLevel::SOFTWARE);
    km::KeyMintHardwareInfo info;
    auto status = device->getHardwareInfo(&info);
    if (!status.isOk() || info.securityLevel != km::SecurityLevel::SOFTWARE || info.versionNumber != 4)
        return 1;
    const std::string name = std::string(km::IKeyMintDevice::descriptor) + "/software";
    if (AServiceManager_addService(device->asBinder().get(), name.c_str()) != STATUS_OK)
        return 2;
    std::fprintf(stderr, "ORIGINAL_KEYMINT_V4_SOFTWARE_REGISTERED NOT_KEY_OR_AUTH_OR_APK_ACCEPTANCE\n");
    ABinderProcess_joinThreadPool();
    return 3;
}
