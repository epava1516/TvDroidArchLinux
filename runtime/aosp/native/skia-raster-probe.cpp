// Verify original Skia raster drawing before wiring HWUI to ART and Wayland.
#include "include/core/SkCanvas.h"
#include "include/core/SkColor.h"
#include "include/core/SkImageInfo.h"
#include "include/core/SkPaint.h"
#include "include/core/SkPixmap.h"
#include "include/core/SkSurface.h"

#include <cstdio>
#include <vector>

int main(int argc, char** argv) {
    if (argc != 2) {
        std::fprintf(stderr, "usage: skia-raster-probe OUTPUT.ppm\n");
        return 2;
    }
    constexpr int width = 64, height = 48;
    constexpr SkColor background = 0xff102030, red = 0xffcc4422, blue = 0xff2255cc;
    auto surface = SkSurface::MakeRasterN32Premul(width, height);
    if (!surface) return 3;
    auto* canvas = surface->getCanvas();
    canvas->clear(background);
    SkPaint paint;
    paint.setAntiAlias(false);
    paint.setColor(red);
    canvas->drawRect(SkRect::MakeXYWH(8, 6, 32, 24), paint);
    canvas->save();
    canvas->clipRect(SkRect::MakeXYWH(18, 14, 6, 6));
    canvas->translate(2, 3);
    paint.setColor(blue);
    canvas->drawRect(SkRect::MakeXYWH(14, 9, 8, 8), paint);
    canvas->restore();

    SkPixmap pixmap;
    if (!surface->peekPixels(&pixmap)) return 4;
    std::vector<unsigned char> rgba(width * height * 4);
    auto info = SkImageInfo::Make(width, height, kRGBA_8888_SkColorType, kUnpremul_SkAlphaType);
    if (!surface->readPixels(info, rgba.data(), width * 4, 0, 0)) return 5;
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            SkColor expected = background;
            if (x >= 8 && x < 40 && y >= 6 && y < 30) expected = red;
            if (x >= 18 && x < 24 && y >= 14 && y < 20) expected = blue;
            const auto* pixel = rgba.data() + (y * width + x) * 4;
            if (pixmap.getColor(x, y) != expected || pixel[0] != SkColorGetR(expected)
                    || pixel[1] != SkColorGetG(expected) || pixel[2] != SkColorGetB(expected)
                    || pixel[3] != 255) {
                std::fprintf(stderr, "pixel mismatch at %d,%d\n", x, y);
                return 6;
            }
        }
    }
    FILE* file = std::fopen(argv[1], "wb");
    if (!file) return 7;
    bool ok = std::fprintf(file, "P6\n%d %d\n255\n", width, height) > 0;
    for (int i = 0; i < width * height && ok; ++i) {
        ok = std::fwrite(rgba.data() + i * 4, 1, 3, file) == 3;
    }
    if (std::fclose(file) != 0 || !ok) return 8;
    std::printf("ORIGINAL_SKIA_RASTER_OK pixels=%d clip=1 translate=1 rgba_readback=1\n", width * height);
    return 0;
}
