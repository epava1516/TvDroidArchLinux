package java.lang.ref;

/** Compile-only Android libcore declaration; never included in framework.jar or DEX. */
public abstract class Reference<T> {
    public native T get();
    public native boolean refersTo(T value);
    public native void clear();
    public native boolean enqueue();
    public native boolean isEnqueued();
    public static native void reachabilityFence(Object value);
}
