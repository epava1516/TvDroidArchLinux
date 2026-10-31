#include <ui/Rect.h>
#include <ui/Region.h>
#include <ui/Transform.h>
#include <ui/Fence.h>
#include <fstream>
#include <iostream>
#include <string>
#define CHECK(x) do { if (!(x)) { std::cerr << "FAILED " << #x << '\n'; return 1; } } while (0)
int main() {
    using namespace android;
    Region outer(Rect(0,0,100,100));
    Region cut=outer.subtract(Rect(25,25,75,75));
    CHECK(cut.contains(10,10)); CHECK(!cut.contains(50,50));
    CHECK(cut.getBounds()==Rect(0,0,100,100));
    Region moved=cut.translate(5,7);
    CHECK(moved.getBounds()==Rect(5,7,105,107));
    CHECK(!moved.contains(55,57));
    ui::Transform translation; translation.set(5.0f,7.0f);
    Rect input(2,3,12,23); Rect transformed=translation.transform(input);
    CHECK(transformed==Rect(7,10,17,30));
    CHECK(translation.inverse().transform(transformed)==input);
    std::cout << "REGION_BOOLEAN_TRANSLATION_AND_TRANSFORM_INVERSE_OK\n";
    CHECK(!Fence::NO_FENCE->isValid());
    CHECK(Fence::NO_FENCE->wait(0)==0);
    CHECK(Fence::NO_FENCE->getSignalTime()==Fence::SIGNAL_TIME_INVALID);
    std::cout << "NO_FENCE_SENTINEL_SEMANTICS_OK_NOT_REAL_SYNC_FILE\n";
    std::ifstream maps("/proc/self/maps"); std::string line; bool loaded=false;
    while (std::getline(maps,line)) if (line.find("/data/libui.so")!=std::string::npos) loaded=true;
    CHECK(loaded); std::cout << "SOURCE_LIBUI_MAPPED=/data/libui.so\n";
    return 0;
}
