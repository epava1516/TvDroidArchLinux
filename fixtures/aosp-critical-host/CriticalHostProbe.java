package org.archtv.aospprobe;

import dalvik.annotation.optimization.CriticalNative;

public final class CriticalHostProbe {
    @CriticalNative private static native long integer(long a, int b, boolean flip);
    @CriticalNative private static native double floating(double a, float b, long c);
    @CriticalNative private static native boolean compare(float a, double b);
    @CriticalNative private static native float scale(float a, float b);
    @CriticalNative private static native int lower(long a, int b);
    @CriticalNative private static native void record(long value);
    @CriticalNative private static native long read();
    @CriticalNative private static native double wide(long a, int b, float c, double d,
            long e, int f, float g, double h, long i, int j, float k, double l);
    private static void exact(double actual, double expected) {
        if (Double.doubleToLongBits(actual) != Double.doubleToLongBits(expected))
            throw new AssertionError(actual + " != " + expected);
    }
    public static void main(String[] args) {
        System.load(args[0]);
        long[] longs = {0, 1, -1, Long.MIN_VALUE, Long.MAX_VALUE, 0x123456789abcdef0L};
        int[] ints = {0, 1, -1, Integer.MIN_VALUE, Integer.MAX_VALUE};
        int calls = 0;
        for (long a : longs) for (int b : ints) for (boolean flip : new boolean[]{false,true}) {
            long expected = a ^ (((long)b & 0xffffffffL) << 32);
            if (integer(a, b, flip) != (flip ? ~expected : expected)) throw new AssertionError("integer");
            record(a);
            if (read() != a) throw new AssertionError("void/store/read");
            if (lower(a,b) != ((int)a ^ b)) throw new AssertionError("int return");
            calls += 4;
        }
        for (int i = -256; i <= 256; ++i) {
            double a = i * .25;
            float b = i * .5f;
            long c = i * 1027L;
            exact(floating(a,b,c), a + (double)b * .5 + (double)(c % 1024));
            if (compare(b,a) != (b < a)) throw new AssertionError("boolean");
            if (Float.floatToIntBits(scale(b,i*.25f)) != Float.floatToIntBits(b*(i*.25f)))
                throw new AssertionError("float return");
            exact(wide(i,2,b,a,3,4,b*.5f,a*.25,5,6,b*.25f,a*.5),
                    (double)i + 2.*2 + 3.*b + 4.*a + 5.*3 + 6.*4 + 7.*(b*.5f)
                    + 8.*(a*.25) + 9.*5 + 10.*6 + 11.*(b*.25f) + 12.*(a*.5));
            calls += 4;
        }
        exact(floating(Double.POSITIVE_INFINITY, 1, 0), Double.POSITIVE_INFINITY);
        exact(floating(Double.NaN, 1, 0), Double.NaN);
        if (compare(Float.NaN, 0) || compare(0, Double.NaN)) throw new AssertionError("NaN comparison");
        if (scale(Float.POSITIVE_INFINITY,1) != Float.POSITIVE_INFINITY
                || !Float.isNaN(scale(Float.NaN,1))) throw new AssertionError("float special");
        calls += 6;
        System.out.println("ART_CRITICAL_HOST_ABI_OK signatures=8 calls="+calls);
    }
}
