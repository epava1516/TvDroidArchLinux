package org.archtv.aospprobe;
public final class QueueLinkProbe {
 public static void main(String[] args) throws Exception {
  System.out.println("ART_FD_GETINT="+java.io.FileDescriptor.class.getDeclaredMethod("getInt$").getReturnType().getName());
  android.os.Looper.prepare();
  System.out.println("AOSP_LOOPER_PREPARED");
 }
}
