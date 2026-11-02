// Component ABI/cryptography diagnosis only. Not Android Keystore, authentication,
// isolation, persistence across cohort teardown, or APK compatibility acceptance.
#include <AndroidKeyMintDevice.h>
#include <aidl/android/hardware/security/keymint/ErrorCode.h>
#include <cstdio>
#include <fstream>

namespace km = aidl::android::hardware::security::keymint;
using Bytes = std::vector<uint8_t>;
using Params = std::vector<km::KeyParameter>;

static void require(bool ok, const char* step) {
    if (!ok) { std::fprintf(stderr, "KEYMINT_COMPONENT_FAILED %s\n", step); std::exit(1); }
}
static km::KeyParameter number(km::Tag tag, int value) {
    return {tag, km::KeyParameterValue::make<km::KeyParameterValue::integer>(value)};
}
static Params operationParams() {
    return {{km::Tag::BLOCK_MODE, km::KeyParameterValue::make<km::KeyParameterValue::blockMode>(km::BlockMode::GCM)},
            {km::Tag::PADDING, km::KeyParameterValue::make<km::KeyParameterValue::paddingMode>(km::PaddingMode::NONE)},
            number(km::Tag::MAC_LENGTH, 128)};
}
static void save(std::ofstream& out, const Bytes& data) {
    uint32_t size = data.size(); out.write(reinterpret_cast<const char*>(&size), sizeof(size));
    out.write(reinterpret_cast<const char*>(data.data()), data.size()); require(out.good(), "save");
}
static Bytes load(std::ifstream& in) {
    uint32_t size = 0; in.read(reinterpret_cast<char*>(&size), sizeof(size));
    require(in.good() && size > 0 && size <= 1048576, "read length");
    Bytes data(size); in.read(reinterpret_cast<char*>(data.data()), size); require(in.good(), "read payload"); return data;
}
int main(int argc, char** argv) {
    require(argc == 3, "usage: write|read private-state-path");
    auto device = km::CreateKeyMintDevice(km::SecurityLevel::SOFTWARE);
    km::KeyMintHardwareInfo info;
    require(device->getHardwareInfo(&info).isOk() && info.securityLevel == km::SecurityLevel::SOFTWARE && info.versionNumber == 4, "honest software v4 metadata");
    const Bytes plain = {'a','r','c','h','t','v','-','c','r','y','p','t','o'};
    if (std::string(argv[1]) == "write") {
        Params params = {
            {km::Tag::ALGORITHM, km::KeyParameterValue::make<km::KeyParameterValue::algorithm>(km::Algorithm::AES)},
            number(km::Tag::KEY_SIZE, 256), number(km::Tag::MIN_MAC_LENGTH, 128),
            {km::Tag::PURPOSE, km::KeyParameterValue::make<km::KeyParameterValue::keyPurpose>(km::KeyPurpose::ENCRYPT)},
            {km::Tag::PURPOSE, km::KeyParameterValue::make<km::KeyParameterValue::keyPurpose>(km::KeyPurpose::DECRYPT)},
            {km::Tag::BLOCK_MODE, km::KeyParameterValue::make<km::KeyParameterValue::blockMode>(km::BlockMode::GCM)},
            {km::Tag::PADDING, km::KeyParameterValue::make<km::KeyParameterValue::paddingMode>(km::PaddingMode::NONE)},
            {km::Tag::NO_AUTH_REQUIRED, km::KeyParameterValue::make<km::KeyParameterValue::boolValue>(true)}};
        km::KeyCreationResult key; require(device->generateKey(params, std::nullopt, &key).isOk() && !key.keyBlob.empty(), "generate AES256");
        for (const auto& c : key.keyCharacteristics) require(c.securityLevel == km::SecurityLevel::SOFTWARE || c.securityLevel == km::SecurityLevel::KEYSTORE, "no hardware characteristics");
        km::BeginResult operation; require(device->begin(km::KeyPurpose::ENCRYPT, key.keyBlob, operationParams(), std::nullopt, &operation).isOk(), "begin encrypt");
        Bytes nonce;
        for (const auto& p : operation.params) if (p.tag == km::Tag::NONCE) nonce = p.value.get<km::KeyParameterValue::blob>();
        require(!nonce.empty() && operation.operation, "generated nonce/operation");
        Bytes cipher; require(operation.operation->finish(plain, std::nullopt, std::nullopt, std::nullopt, std::nullopt, &cipher).isOk() && cipher != plain, "encrypt");
        std::ofstream out(argv[2], std::ios::binary); save(out, key.keyBlob); save(out, nonce); save(out, cipher);
        std::puts("KEYMINT_COMPONENT_ENCRYPTED_AND_SAVED SOFTWARE v4 NOT_KEYSTORE_OR_APK_ACCEPTANCE");
    } else {
        require(std::string(argv[1]) == "read", "unknown mode");
        std::ifstream in(argv[2], std::ios::binary); Bytes blob = load(in), nonce = load(in), cipher = load(in);
        Params params = operationParams(); params.push_back({km::Tag::NONCE, km::KeyParameterValue::make<km::KeyParameterValue::blob>(nonce)});
        km::BeginResult op; require(device->begin(km::KeyPurpose::DECRYPT, blob, params, std::nullopt, &op).isOk() && op.operation, "reopened begin decrypt");
        Bytes output; require(op.operation->finish(cipher, std::nullopt, std::nullopt, std::nullopt, std::nullopt, &output).isOk() && output == plain, "reopened decrypt");
        require(device->begin(km::KeyPurpose::DECRYPT, blob, params, std::nullopt, &op).isOk() && op.operation, "negative begin");
        cipher.back() ^= 1;
        auto bad = op.operation->finish(cipher, std::nullopt, std::nullopt, std::nullopt, std::nullopt, &output);
        require(!bad.isOk() && bad.getServiceSpecificError() == static_cast<int>(km::ErrorCode::VERIFICATION_FAILED), "reject modified GCM tag");
        blob.back() ^= 1;
        require(!device->begin(km::KeyPurpose::DECRYPT, blob, params, std::nullopt, &op).isOk(), "reject modified key blob");
        std::puts("KEYMINT_COMPONENT_REOPEN_DECRYPT_AND_NEGATIVES_PASSED SOFTWARE v4 NOT_KEYSTORE_OR_APK_ACCEPTANCE");
    }
}
