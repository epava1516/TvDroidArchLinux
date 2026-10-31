// Linux build-time wrapper around the pinned original AOSP property libraries.
// This is not an Android property server or an implementation of property APIs.
#include <property_info_serializer/property_info_serializer.h>
#include <property_info_parser/property_info_parser.h>
#include <fcntl.h>
#include <unistd.h>
#include <cerrno>
#include <cstring>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <vector>

int main(int argc, char** argv) {
  using namespace android::properties;
  if (argc >= 2 && std::string(argv[1]) == "--inspect") {
    if (argc < 4) { std::cerr << "Inspection requires file and property names\n"; return 2; }
    PropertyInfoAreaFile area;
    if (!area.LoadPath(argv[2])) {
      std::cerr << "Original PropertyInfoAreaFile rejected input\n";
      return 2;
    }
    for (int i = 3; i < argc; ++i) {
      const char *context = nullptr, *type = nullptr;
      area->GetPropertyInfo(argv[i], &context, &type);
      std::cout << argv[i] << '\t' << (context ? context : "<absent>")
                << '\t' << (type ? type : "<absent>") << '\n';
    }
    return 0;
  }
  if (argc < 3) {
    std::cerr << "Usage: property-info OUTPUT CONTEXTS...\n"
                 "       property-info --inspect FILE PROPERTY...\n";
    return 2;
  }
  std::vector<PropertyInfoEntry> entries;
  for (int i = 2; i < argc; ++i) {
    std::ifstream input(argv[i]);
    if (!input) { std::cerr << "Cannot read " << argv[i] << '\n'; return 2; }
    std::string text((std::istreambuf_iterator<char>(input)), {});
    std::vector<std::string> errors;
    ParsePropertyInfoFile(text, true, &entries, &errors);
    if (!errors.empty()) {
      for (const auto& error : errors) std::cerr << argv[i] << ": " << error << '\n';
      return 2;
    }
  }
  std::string blob, error;
  if (!BuildTrie(entries, "u:object_r:default_prop:s0", "string", &blob, &error)) {
    std::cerr << error << '\n'; return 2;
  }
  int fd = open(argv[1], O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC, 0644);
  if (fd < 0) { std::cerr << strerror(errno) << '\n'; return 2; }
  size_t written = 0;
  while (written < blob.size()) {
    ssize_t count = write(fd, blob.data() + written, blob.size() - written);
    if (count < 0 && errno == EINTR) continue;
    if (count <= 0) { close(fd); std::cerr << "Write failed; partial output retained\n"; return 2; }
    written += static_cast<size_t>(count);
  }
  if (close(fd) != 0) { std::cerr << "Close failed\n"; return 2; }
  std::cout << "entries=" << entries.size() << " bytes=" << blob.size() << '\n';
  return 0;
}
