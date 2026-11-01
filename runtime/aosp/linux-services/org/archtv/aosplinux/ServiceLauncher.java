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
            // Original ZygoteInit.createPathClassLoader: boot parent, native
            // library paths and a shared platform namespace for trusted services.
            // Tenant APKs must never use this privileged loader.
            String libraries = System.getProperty("java.library.path");
            int target = Class.forName("android.os.Build$VERSION_CODES")
                    .getField("CUR_DEVELOPMENT").getInt(null);
            Class<?> factory = Class.forName("com.android.internal.os.ClassLoaderFactory");
            ClassLoader loader = (ClassLoader) factory.getMethod("createClassLoader",
                    String.class, String.class, String.class, ClassLoader.class,
                    int.class, boolean.class, String.class).invoke(null,
                    original + ":/vendor/framework/archtv-selected-services.jar",
                    libraries, libraries, ClassLoader.getSystemClassLoader().getParent(),
                    target, true, null);
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
