package org.archtv.aospprobe;

import android.os.SystemClock;

public final class ClockNativeProbe {
    public static void main(String[] args) {
        System.load(args[0]);
        long before = SystemClock.uptimeNanos();
        long millis = SystemClock.uptimeMillis();
        long after = SystemClock.uptimeNanos();
        if (before/1000000 > millis || millis > after/1000000) throw new AssertionError("Uptime units");
        before = SystemClock.elapsedRealtimeNanos();
        millis = SystemClock.elapsedRealtime();
        after = SystemClock.elapsedRealtimeNanos();
        if (before/1000000 > millis || millis > after/1000000) throw new AssertionError("Boottime units");
        before = SystemClock.currentThreadTimeMicro();
        millis = SystemClock.currentThreadTimeMillis();
        after = SystemClock.currentThreadTimeMicro();
        if (before/1000 > millis || millis > after/1000) throw new AssertionError("Thread CPU units");
        before = System.currentTimeMillis();
        long micro = SystemClock.currentTimeMicro();
        after = System.currentTimeMillis();
        if (before > micro/1000 || micro/1000 > after) throw new AssertionError("Wall clock units");
        before = SystemClock.uptimeMillis();
        SystemClock.sleep(20);
        if (SystemClock.uptimeMillis() < before+20) throw new AssertionError("Sleep returned early");
        Thread.currentThread().interrupt();
        SystemClock.sleep(1);
        if (!Thread.interrupted()) throw new AssertionError("Sleep lost interrupt status");
        System.out.println("AOSP_CLOCK_JNI_OK");
    }
}
