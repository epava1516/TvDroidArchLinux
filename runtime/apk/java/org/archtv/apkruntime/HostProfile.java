package org.archtv.apkruntime;

import android.os.SystemProperties;

/** Explicit laboratory target, not a claim of complete Android API/NDK compatibility. */
final class HostProfile {
    private HostProfile() {}
    private static native void nativeInitialize();
    static void initialize() {
        nativeInitialize();
        if (SystemProperties.getInt("ro.build.version.sdk", -1) != 33
                || !"x86_64".equals(SystemProperties.get("ro.product.cpu.abilist64")))
            throw new IllegalStateException("Unsupported ART/framework host profile");
        System.err.println("APK_HOST_PROFILE sdk=33 abi=x86_64");
    }
}
