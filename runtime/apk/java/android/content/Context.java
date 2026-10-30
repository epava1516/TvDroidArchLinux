package android.content;

import org.archtv.apkruntime.AppEnvironment;

public abstract class Context {
    public static final int MODE_PRIVATE = 0;
    public final String getString(int resourceId) {
        return AppEnvironment.current().resources.getString(resourceId);
    }
    public SharedPreferences getSharedPreferences(String name, int mode) {
        if (mode != MODE_PRIVATE) throw new UnsupportedOperationException("Only MODE_PRIVATE is supported");
        return AppEnvironment.current().preferences(name);
    }
}
