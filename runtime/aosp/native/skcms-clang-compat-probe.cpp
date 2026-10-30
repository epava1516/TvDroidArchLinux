#include "skcms-clang-compat.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uint32_t reference(uint16_t half) {
    uint32_t sign = uint32_t(half & 0x8000) << 16;
    uint32_t exponent = (half >> 10) & 31;
    uint32_t mantissa = half & 1023;
    if (exponent == 31) {
        return sign | 0x7f800000 | (mantissa << 13) | (mantissa ? 0x400000 : 0);
    }
    if (exponent) return sign | ((exponent + 112) << 23) | (mantissa << 13);
    if (!mantissa) return sign;
    int power = -14;
    while (!(mantissa & 1024)) { mantissa <<= 1; --power; }
    return sign | (uint32_t(power + 127) << 23) | ((mantissa & 1023) << 13);
}

__attribute__((target("avx2,f16c"))) static int check() {
    typedef int16_t __attribute__((vector_size(16))) I16;
    for (uint32_t first = 0; first < 65536; first += 8) {
        I16 input;
        for (int lane = 0; lane < 8; ++lane) input[lane] = int16_t(first + lane);
        __m256 converted = __builtin_ia32_vcvtph2ps256(input);
        float output[8];
        _mm256_storeu_ps(output, converted);
        for (int lane = 0; lane < 8; ++lane) {
            uint32_t bits;
            memcpy(&bits, &output[lane], sizeof(bits));
            uint32_t expected = reference(uint16_t(first + lane));
            if (bits != expected) {
                fprintf(stderr, "half=%04x float=%08x expected=%08x\n", first + lane, bits, expected);
                return 1;
            }
        }
    }
    puts("SKCMS_F16C_COMPAT_OK half_patterns=65536 simd=1");
    return 0;
}

int main() {
    if (!__builtin_cpu_supports("avx2") || !__builtin_cpu_supports("f16c")) {
        fputs("F16C_COMPAT_UNTESTED CPU lacks AVX2/F16C\n", stderr);
        return 77;
    }
    return check();
}
