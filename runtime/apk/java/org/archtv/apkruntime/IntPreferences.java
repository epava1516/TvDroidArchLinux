package org.archtv.apkruntime;

import android.content.SharedPreferences;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.attribute.PosixFilePermissions;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;

/** Integer-only preferences. Atomic replace; no Android XML interchange claim. */
final class IntPreferences implements SharedPreferences {
    private final Path path;
    private final Map<String, Integer> values = new HashMap<String, Integer>();
    IntPreferences(Path path) {
        this.path = path;
        if (Files.exists(path)) {
            try {
                if (Files.size(path) > 1024*1024) throw new IOException("Preferences too large");
                Properties properties = new Properties();
                try (FileInputStream stream = new FileInputStream(path.toFile())) { properties.load(stream); }
                for (String key : properties.stringPropertyNames())
                    values.put(key, Integer.valueOf(properties.getProperty(key)));
            } catch (IOException | NumberFormatException failure) {
                throw new IllegalStateException("Cannot read preferences: "+path, failure);
            }
        }
    }
    public synchronized int getInt(String key, int defaultValue) {
        Integer value = values.get(key);
        return value == null ? defaultValue : value;
    }
    public Editor edit() { return new Transaction(); }
    private final class Transaction implements Editor {
        private final Map<String, Integer> updates = new HashMap<String, Integer>();
        public Editor putInt(String key, int value) {
            if (key == null) throw new NullPointerException("key");
            if (key.length() > 4096) throw new IllegalArgumentException("Preference key too long");
            updates.put(key, value);
            return this;
        }
        public boolean commit() {
            synchronized (IntPreferences.this) {
                values.putAll(updates);
                updates.clear();
                Path temporary = null;
                try {
                    temporary = Files.createTempFile(path.getParent(), ".preferences-", ".tmp",
                        PosixFilePermissions.asFileAttribute(PosixFilePermissions.fromString("rw-------")));
                    Properties properties = new Properties();
                    for (Map.Entry<String, Integer> entry : values.entrySet())
                        properties.setProperty(entry.getKey(), entry.getValue().toString());
                    try (FileOutputStream stream = new FileOutputStream(temporary.toFile())) {
                        properties.store(stream, "ArchTV integer preferences v1");
                        stream.getFD().sync();
                    }
                    Files.move(temporary, path, StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
                    return true;
                } catch (IOException failure) {
                    System.err.println("PREFERENCE_COMMIT_FAILED "+failure);
                    return false;
                } finally {
                    if (temporary != null) {
                        try { Files.deleteIfExists(temporary); } catch (IOException failure) {
                            System.err.println("PREFERENCE_TEMP_CLEANUP_FAILED "+failure);
                        }
                    }
                }
            }
        }
    }
}
