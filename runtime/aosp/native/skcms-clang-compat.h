#pragma once

// Original Android 13 skcms names a Clang builtin removed in Clang 23.
// Keep its F16C conversion through the public intrinsic, with the same bits
// and target requirement. The original skcms CPU dispatch remains intact.
#if defined(__clang__) && __clang_major__ >= 23
#include <immintrin.h>
#define __builtin_ia32_vcvtph2ps256(value) \
    _mm256_cvtph_ps((__m128i)(value))
#endif
