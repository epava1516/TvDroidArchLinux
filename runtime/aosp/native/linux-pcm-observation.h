#pragma once

// Explicit known-media diagnostic only. Copies bytes AFTER positive TinyALSA
// acceptance; never changes the source buffer, return value, position or clock.
// Output uses the original Module::dump Binder FD, not new file permissions.
#include <android-base/file.h>
#include <android/binder_status.h>
#include <cerrno>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <mutex>
#include <new>
#include <sstream>
#include <string>
#include <unistd.h>

namespace archtv::pcm_observation {
inline constexpr size_t kLimit = 2 * 1024 * 1024;
inline bool enabled() {
    const char* value = std::getenv("ARCHTV_PCM_OBSERVE_KNOWN_MEDIA");
    return value != nullptr && std::strcmp(value, "1") == 0;
}
struct State {
    std::mutex mutex;
    const void* owner = nullptr;
    std::unique_ptr<unsigned char[]> bytes;
    size_t captured = 0;
    uint64_t totalFrames = 0;
    uint64_t writes = 0;
    uint32_t flags = 0; // 1=truncated, 2=other stream, 4=shape, 8=allocation
    unsigned rate = 0, channels = 0, frameBytes = 0, format = 0;
    int pid = 0, tid = 0, hwError = 0, statusError = 0;
    std::string hwParams, pcmStatus;
};
inline State state;

inline void accepted(const void* owner, const void* data, size_t frames,
                     unsigned frameBytes, unsigned channels, unsigned rate,
                     unsigned format) {
    if (!enabled()) return;
    const std::lock_guard<std::mutex> lock(state.mutex);
    if (state.owner == nullptr) {
        state.owner = owner;
        state.pid = getpid();
        state.tid = gettid();
        state.rate = rate;
        state.channels = channels;
        state.frameBytes = frameBytes;
        state.format = format;
        state.bytes.reset(new (std::nothrow) unsigned char[kLimit]);
        if (!state.bytes) state.flags |= 8;
        if (!android::base::ReadFileToString(
                    "/proc/asound/card0/pcm0p/sub0/hw_params", &state.hwParams))
            state.hwError = errno;
        if (!android::base::ReadFileToString(
                    "/proc/asound/card0/pcm0p/sub0/status", &state.pcmStatus))
            state.statusError = errno;
        if (state.hwParams.size() > 4096 || state.pcmStatus.size() > 4096) {
            state.flags |= 4;
            state.hwParams.clear();
            state.pcmStatus.clear();
        }
    }
    if (state.owner != owner) {
        state.flags |= 2;
        return;
    }
    state.totalFrames += frames;
    ++state.writes;
    // Selected x86_64 PCM16 stereo48k path only; no synthetic conversion.
    if (frameBytes != 4 || channels != 2 || rate != 48000 || format != 0 ||
        frameBytes != state.frameBytes || channels != state.channels ||
        rate != state.rate || format != state.format) {
        state.flags |= 4;
        return;
    }
    if (!state.bytes) return;
    const size_t available = (kLimit - state.captured) / frameBytes;
    const size_t count = frames < available ? frames : available;
    std::memcpy(state.bytes.get() + state.captured, data, count * frameBytes);
    state.captured += count * frameBytes;
    if (count != frames) state.flags |= 1;
}

inline bool writeAll(int fd, const void* bytes, size_t count) {
    const auto* data = static_cast<const unsigned char*>(bytes);
    while (count != 0) {
        const ssize_t n = ::write(fd, data, count);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) return false;
        data += n;
        count -= static_cast<size_t>(n);
    }
    return true;
}

inline binder_status_t dump(int fd) {
    if (!enabled()) return STATUS_PERMISSION_DENIED;
    std::unique_ptr<unsigned char[]> snapshot;
    std::string header, hwParams, pcmStatus;
    size_t size = 0;
    {
        const std::lock_guard<std::mutex> lock(state.mutex);
        size = state.captured;
        if (size != 0) {
            snapshot.reset(new (std::nothrow) unsigned char[size]);
            if (!snapshot) return STATUS_NO_MEMORY;
            std::memcpy(snapshot.get(), state.bytes.get(), size);
        }
        hwParams = state.hwParams;
        pcmStatus = state.pcmStatus;
        std::ostringstream out;
        out << "ARCHTV_ACCEPTED_PCM_V1\n"
            << state.rate << ' ' << state.channels << ' ' << state.frameBytes << ' '
            << state.format << ' ' << state.totalFrames << ' ' << size << ' '
            << state.writes << ' ' << state.flags << ' ' << hwParams.size() << ' '
            << pcmStatus.size() << ' ' << state.hwError << ' ' << state.statusError
            << ' ' << state.pid << ' ' << state.tid << '\n';
        header = out.str();
    }
    // Snapshot is immutable and the capture is not consumed by repeated dumps.
    if (!writeAll(fd, header.data(), header.size()) ||
        !writeAll(fd, hwParams.data(), hwParams.size()) ||
        !writeAll(fd, pcmStatus.data(), pcmStatus.size()) ||
        (size != 0 && !writeAll(fd, snapshot.get(), size)))
        return STATUS_FAILED_TRANSACTION;
    return STATUS_OK;
}
} // namespace archtv::pcm_observation
