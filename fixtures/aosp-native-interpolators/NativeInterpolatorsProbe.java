package org.archtv.aospprobe;

import android.graphics.animation.NativeInterpolatorFactory;
import android.view.animation.AccelerateDecelerateInterpolator;
import android.view.animation.LinearInterpolator;

public final class NativeInterpolatorsProbe {
    private static native float evaluate(long handle, float input);
    private static native void release(long handle);
    private static int objects;
    private static final float[] INPUT = {0f, .25f, .5f, .75f, 1f};
    private static void near(float actual, float expected) {
        if (!Float.isFinite(actual) || Math.abs(actual - expected) > .0001f)
            throw new AssertionError(actual + " != " + expected);
    }
    private static void check(long handle, float... expected) {
        if (handle == 0 || expected.length != INPUT.length) throw new AssertionError("allocation");
        try {
            for (int i = 0; i < INPUT.length; ++i) near(evaluate(handle, INPUT[i]), expected[i]);
        } finally { release(handle); }
        objects++;
    }
    public static void main(String[] args) {
        System.load(args[0]);
        try { evaluate(0, .5f); throw new AssertionError("null accepted"); }
        catch (IllegalArgumentException expected) {}
        for (int cycle = 0; cycle < 20; ++cycle) {
            check(NativeInterpolatorFactory.createAccelerateDecelerateInterpolator(), 0f,.1464466f,.5f,.8535534f,1f);
            check(NativeInterpolatorFactory.createAccelerateInterpolator(2f), 0f,.00390625f,.0625f,.31640625f,1f);
            check(NativeInterpolatorFactory.createAnticipateInterpolator(2f), 0f,-.078125f,-.125f,.140625f,1f);
            check(NativeInterpolatorFactory.createAnticipateOvershootInterpolator(2f), 0f,-.0625f,.5f,1.0625f,1f);
            check(NativeInterpolatorFactory.createBounceInterpolator(), 0f,.6301154f,.7015927f,.9009076f,1.0000545f);
            check(NativeInterpolatorFactory.createCycleInterpolator(1f), 0f,1f,0f,-1f,0f);
            check(NativeInterpolatorFactory.createDecelerateInterpolator(1f), 0f,.4375f,.75f,.9375f,1f);
            check(NativeInterpolatorFactory.createLinearInterpolator(), 0f,.25f,.5f,.75f,1f);
            check(NativeInterpolatorFactory.createOvershootInterpolator(2f), 0f,.859375f,1.125f,1.078125f,1f);
            check(NativeInterpolatorFactory.createPathInterpolator(new float[]{0f,.5f,1f}, new float[]{0f,.25f,1f}),
                    0f,.125f,.25f,.625f,1f);
            check(NativeInterpolatorFactory.createLutInterpolator(new float[]{0f,.25f,1f}), 0f,.125f,.25f,.625f,1f);
        }
        if (NativeInterpolatorFactory.createLutInterpolator(new float[0]) != 0)
            throw new AssertionError("empty LUT changed original result");
        LinearInterpolator linear = new LinearInterpolator();
        AccelerateDecelerateInterpolator eased = new AccelerateDecelerateInterpolator();
        long l = linear.createNativeInterpolator(), e = eased.createNativeInterpolator();
        if (l == 0 || e == 0) throw new AssertionError("original Java factory");
        try {
            for (int i = 0; i <= 1000; ++i) {
                float t = i / 1000f;
                near(evaluate(l, t), linear.getInterpolation(t));
                near(evaluate(e, t), eased.getInterpolation(t));
            }
        } finally { release(l); release(e); }
        objects += 2;
        System.out.println("AOSP_NATIVE_INTERPOLATORS_OK factories=11 objects="+objects+" samples=3102 java_parity=2");
    }
}
