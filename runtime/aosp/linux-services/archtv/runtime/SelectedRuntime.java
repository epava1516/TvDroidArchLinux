package archtv.runtime;

/** Linux-selected entry after the original Zygote system-server fork and hooks. */
public final class SelectedRuntime {
    private static String hex(String value) throws java.io.UnsupportedEncodingException {
        final char[] digits = "0123456789abcdef".toCharArray();
        byte[] bytes = value.getBytes("UTF-8");
        StringBuilder result = new StringBuilder(bytes.length * 2);
        for (byte item : bytes) {
            int b = item & 255;
            result.append(digits[b >>> 4]).append(digits[b & 15]);
        }
        return result.toString();
    }

    // Read our own kernel metadata instead of granting a Linux observer access
    // to other domains. These records are evidence, never service readiness.
    private static void observeKernelState(int pid) {
        try (java.io.BufferedReader reader = new java.io.BufferedReader(
                new java.io.FileReader("/proc/self/status"))) {
            String line;
            int chars = 0;
            while ((line = reader.readLine()) != null) {
                chars += line.length() + 1;
                if (chars > 16384) throw new java.io.IOException("status observation bound");
                if (line.matches("^(Uid|Gid|Groups|CapPrm|CapEff|CapBnd|NoNewPrivs):.*")) {
                    System.err.println("ORIGINAL_SYSTEMSERVER_STATUS_V1 pid=" + pid
                            + " line_hex=" + hex(line));
                }
            }
        } catch (java.io.IOException error) {
            System.err.println("ORIGINAL_SYSTEMSERVER_STATUS_ERROR_V1 pid=" + pid
                    + " error=" + error.getClass().getName());
        }
        int count = 0;
        try (java.io.BufferedReader reader = new java.io.BufferedReader(
                new java.io.FileReader("/proc/self/maps"))) {
            String line;
            int chars = 0;
            while ((line = reader.readLine()) != null) {
                chars += line.length() + 1;
                if (chars > 1048576) throw new java.io.IOException("maps observation bound");
                String[] fields = line.trim().split("\\s+", 6);
                if (fields.length != 6) continue;
                String path = fields[5];
                if (!(path.contains("/data/misc/apexdata/com.android.art/")
                        || path.contains("/system/framework/")
                        || path.contains("/apex/com.android.art/")
                        || path.contains("memfd:boot") || path.contains("dalvik-boot"))) continue;
                if (!(path.contains(".art") || path.contains(".oat") || path.contains(".vdex"))) continue;
                if (++count > 256) throw new java.io.IOException("image record bound");
                // Do not publish virtual addresses or memory contents. Preserve
                // actual pathname, inode, device, offset and access permissions.
                System.err.println("ORIGINAL_SYSTEMSERVER_IMAGE_MAP_V1 pid=" + pid
                        + " perms=" + fields[1] + " offset=" + fields[2]
                        + " dev=" + fields[3] + " inode=" + fields[4]
                        + " path_hex=" + hex(path));
            }
            System.err.println("ORIGINAL_SYSTEMSERVER_IMAGE_MAP_END_V1 pid=" + pid
                    + " records=" + count + " complete=1 NOT_IMAGE_OR_APK_ACCEPTANCE");
        } catch (java.io.IOException error) {
            System.err.println("ORIGINAL_SYSTEMSERVER_IMAGE_MAP_ERROR_V1 pid=" + pid
                    + " records=" + count + " error=" + error.getClass().getName());
        }
    }

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
        int pid = ((Integer) Class.forName("android.system.Os").getMethod("getpid").invoke(null));
        observeKernelState(pid);
        org.archtv.aosplinux.ServiceLauncher.main(new String[]{"--packages"});
    }
}
