package org.archtv.aospprobe;

import android.os.Binder;
import android.os.Process;
import android.os.SystemProperties;
import android.system.Os;

public final class LocalContextProbe {
    public static void main(String[] args) throws Exception {
        System.load(args[0]);
        if (Process.myUid() != Os.getuid() || Process.myPid() != Os.getpid()
                || Binder.getCallingUid() != Os.getuid() || Binder.getCallingPid() != Os.getpid())
            throw new AssertionError("Local process identity");
        long token = Binder.clearCallingIdentity();
        Binder.restoreCallingIdentity(token);
        if (Binder.getCallingUid() != Os.getuid() || Binder.getCallingPid() != Os.getpid()
                || Binder.isDirectlyHandlingTransaction()) throw new AssertionError("Identity restoration");
        try {
            Binder.getCallingUidOrThrow();
            throw new AssertionError("No incoming Binder transaction exists");
        } catch (IllegalStateException expected) { }
        if (SystemProperties.getInt("archtv.queue.test", 17) != 42
                || SystemProperties.getInt("archtv.queue.absent", 17) != 17
                || SystemProperties.getInt("archtv.queue.malformed", 17) != 17)
            throw new AssertionError("Read-only host property source");
        try {
            SystemProperties.set("archtv.queue.test", "1");
            throw new AssertionError("Global property writes are not implemented");
        } catch (UnsatisfiedLinkError expected) { }
        System.out.println("AOSP_LOCAL_CONTEXT_OK");
    }
}
