// Compile-only declaration of an ART/libcore private API. Never package this class.
package java.io;
public final class FileDescriptor {
    public native int getInt$();
    public native void setInt$(int value);
}
