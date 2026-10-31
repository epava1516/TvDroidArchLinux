#pragma once
#include <cstdint>
#include <memory>
namespace archtv::aosp {
// One fullscreen output, driven by one thread. Uses the original Wayland client.
// A frame callback is compositor progress, NOT a native sync_file/present fence.
class LinuxWaylandOutput {
 public:
    LinuxWaylandOutput();
    ~LinuxWaylandOutput();
    LinuxWaylandOutput(const LinuxWaylandOutput&)=delete;
    LinuxWaylandOutput& operator=(const LinuxWaylandOutput&)=delete;
    // Consumes a connected AF_UNIX stream FD. Factory admission/MAC is separate.
    bool Connect(int connected_fd);
    int width() const;
    int height() const;
    // Copies packed XRGB8888 rows into a released private SHM buffer, commits,
    // and waits up to 3s for the real callback. Never returns a synthetic fence.
    bool CommitCpu(const uint32_t* pixels,int width,int height,int stride_pixels);
 private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
