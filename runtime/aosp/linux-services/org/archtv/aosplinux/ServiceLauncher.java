package org.archtv.aosplinux;

import java.lang.reflect.InvocationTargetException;

/** Trusted service orchestration, using the original system-server loader factory. */
public final class ServiceLauncher {
    public static void main(String[] args) {
        try {
            // Original SystemServer.run() clears the application growth limit.
            // AndroidRuntime also requires real product heap properties: its
            // default -Xmx16m is appended after app_process command-line options.
            Class<?> vmClass=Class.forName("dalvik.system.VMRuntime");
            Object vm=vmClass.getMethod("getRuntime").invoke(null);
            long growthBefore=Runtime.getRuntime().maxMemory();
            vmClass.getMethod("clearGrowthLimit").invoke(vm);
            long maximumAfter=Runtime.getRuntime().maxMemory();
            if(maximumAfter<growthBefore)throw new IllegalStateException("Original heap growth limit clear reduced budget");
            System.err.println("ORIGINAL_SYSTEMSERVER_HEAP growth_before="+growthBefore+" max_after="+maximumAfter+" NOT_SERVICE_OR_APK_ACCEPTANCE");
            String original = System.getenv("SYSTEMSERVERCLASSPATH");
            if (original == null || original.isEmpty()) {
                throw new IllegalStateException("Original system-server classpath required");
            }
            // Original Zygote JNI already created the system-server and
            // standalone loaders before its security specialization. Reuse the
            // actual original loader; a second prefetch rejects duplicate jars.
            Class<?> zygote=Class.forName("com.android.internal.os.ZygoteInit");
            java.lang.reflect.Method primary=zygote.getDeclaredMethod("getOrCreateSystemServerClassLoader");
            primary.setAccessible(true);
            ClassLoader loader=(ClassLoader)primary.invoke(null);
            if(loader==null || ServiceLauncher.class.getClassLoader()!=loader
                    || Thread.currentThread().getContextClassLoader()!=loader)
                throw new IllegalStateException("Original post-fork loader identity required");
            if(Class.forName("com.android.server.SystemService",false,loader).getClassLoader()!=loader)
                throw new IllegalStateException("Original service classloader identity mismatch");
            System.err.println("ORIGINAL_SYSTEMSERVER_CLASSLOADER_REUSED NOT_SERVICE_OR_APK_ACCEPTANCE");
            if("software-platform-v1".equals(System.getenv("ARCHTV_SOFTWARE_SECURITY_PROFILE"))) {
                // Direct original Binder interface: never convert RemoteException
                // into a fabricated zero secure-user-id or a ready/unlocked flag.
                Class<?> binder=Class.forName("android.os.IBinder");
                Object remote=Class.forName("android.os.ServiceManager").getMethod("waitForService",String.class)
                        .invoke(null,"android.service.gatekeeper.IGateKeeperService");
                if(remote==null)throw new IllegalStateException("Original GateKeeper daemon absent");
                Object gatekeeper=Class.forName("android.service.gatekeeper.IGateKeeperService$Stub")
                        .getMethod("asInterface",binder).invoke(null,remote);
                long secureId=((Long)Class.forName("android.service.gatekeeper.IGateKeeperService")
                        .getMethod("getSecureUserId",int.class).invoke(gatekeeper,0)).longValue();
                int uid=((Integer)Class.forName("android.os.Process").getMethod("myUid").invoke(null)).intValue();
                if(uid!=1000)throw new IllegalStateException("Unexpected service caller UID");
                System.err.println("ORIGINAL_GATEKEEPER_QUERY user=0 secure_user_id="+secureId+" caller_uid="+uid+" NOT_AUTH_OR_UNLOCK_ACCEPTANCE");
            }
            Class<?> entry = Class.forName("org.archtv.aosplinux.SelectedServices", true, loader);
            entry.getMethod("main", String[].class).invoke(null, (Object) args);
            throw new IllegalStateException("Selected service entry returned unexpectedly");
        } catch (Throwable failure) {
            if (failure instanceof InvocationTargetException && failure.getCause() != null) {
                failure = failure.getCause();
            }
            failure.printStackTrace(System.err);
            System.exit(1);
        }
    }
}
