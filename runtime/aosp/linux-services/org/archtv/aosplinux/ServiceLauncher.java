package org.archtv.aosplinux;

import java.lang.reflect.InvocationTargetException;

/** Trusted service orchestration, using the original system-server loader factory. */
public final class ServiceLauncher {
    public static void main(String[] args) {
        try {
            String original = System.getenv("SYSTEMSERVERCLASSPATH");
            if (original == null || original.isEmpty()) {
                throw new IllegalStateException("Original system-server classpath required");
            }
            // Reuse the complete original system-server/standalone loader setup.
            // These helpers create loaders only: no Zygote main, fork or SystemServer boot.
            Class<?> zygote=Class.forName("com.android.internal.os.ZygoteInit");
            java.lang.reflect.Method primary=zygote.getDeclaredMethod("getOrCreateSystemServerClassLoader");
            primary.setAccessible(true);
            ClassLoader systemServer=(ClassLoader)primary.invoke(null);
            if(systemServer==null)throw new IllegalStateException("Original system-server loader absent");
            java.lang.reflect.Method standalone=zygote.getDeclaredMethod("prefetchStandaloneSystemServerJars");
            standalone.setAccessible(true);standalone.invoke(null);
            // Keep our trusted orchestration jar out of SYSTEMSERVERCLASSPATH;
            // parent-first lookup shares the original framework/service identities.
            String libraries=System.getProperty("java.library.path");
            int target=Class.forName("android.os.Build$VERSION_CODES").getField("CUR_DEVELOPMENT").getInt(null);
            Class<?> factory=Class.forName("com.android.internal.os.ClassLoaderFactory");
            ClassLoader loader=(ClassLoader)factory.getMethod("createClassLoader",
                    String.class,String.class,String.class,ClassLoader.class,
                    int.class,boolean.class,String.class).invoke(null,
                    "/vendor/framework/archtv-selected-services.jar",libraries,libraries,systemServer,
                    target,true,null);
            if(Class.forName("com.android.server.SystemService",false,loader).getClassLoader()!=systemServer)
                throw new IllegalStateException("Original service classloader identity mismatch");
            System.err.println("ORIGINAL_SYSTEMSERVER_STANDALONE_LOADERS_INITIALIZED NOT_SERVICE_OR_APK_ACCEPTANCE");
            Thread.currentThread().setContextClassLoader(loader);
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
