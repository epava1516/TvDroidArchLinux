package archtv.runtime;

/** Linux-selected entry after the original Zygote system-server fork and hooks. */
public final class SelectedRuntime {
    public static void main(String[] args) throws Exception {
        String context;
        try (java.io.BufferedReader reader = new java.io.BufferedReader(
                new java.io.FileReader("/proc/self/attr/current"))) {
            context = reader.readLine();
        }
        if (context == null || !context.replace("\u0000", "").equals("u:r:system_server:s0")) {
            throw new IllegalStateException("Original post-fork system_server context required: " + context);
        }
        int uid = ((Integer) Class.forName("android.system.Os").getMethod("getuid").invoke(null));
        if (uid != 1000) throw new IllegalStateException("Original system-server UID required: " + uid);
        System.err.println("ORIGINAL_ZYGOTE_SELECTED_ENTRY uid=" + uid + " context=" + context
                + " NOT_SERVICE_OR_APK_ACCEPTANCE");
        org.archtv.aosplinux.ServiceLauncher.main(new String[]{"--packages"});
    }
}
