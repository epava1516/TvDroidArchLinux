package org.archtv.aospprobe;

import android.os.Looper;
import android.os.MessageQueue;
import android.system.Os;
import java.io.FileDescriptor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.atomic.AtomicInteger;

/** Exercises the JNI boundary, not yet Handler/Looper scheduling. */
public final class NativeQueueProbe {
    private static Method nativeMethod(String name, Class<?>... parameters) throws Exception {
        Method method = MessageQueue.class.getDeclaredMethod(name, parameters);
        method.setAccessible(true);
        return method;
    }
    public static void main(String[] args) throws Exception {
        System.load(args[0]);
        Looper.prepare();
        MessageQueue queue = Looper.myLooper().getQueue();
        Field pointer = MessageQueue.class.getDeclaredField("mPtr");
        pointer.setAccessible(true);
        long handle = pointer.getLong(queue);
        if (handle == 0 || queue.isPolling()) throw new AssertionError("Initial queue state");
        Method poll = nativeMethod("nativePollOnce", long.class, int.class);
        Method wake = nativeMethod("nativeWake", long.class);
        Method events = nativeMethod("nativeSetFileDescriptorEvents", long.class, int.class, int.class);
        wake.invoke(null, handle);
        poll.invoke(queue, handle, 0);
        AtomicReference<Throwable> failure = new AtomicReference<Throwable>();
        Thread worker = new Thread(new Runnable() {
            public void run() {
                try { poll.invoke(queue, handle, 5000); }
                catch (Throwable problem) { failure.set(problem); }
            }
        });
        worker.start();
        long deadline = System.nanoTime()+3000000000L;
        while (!queue.isPolling() && System.nanoTime() < deadline) Thread.sleep(1);
        if (!queue.isPolling()) throw new AssertionError("No live native poll");
        wake.invoke(null, handle);
        worker.join(6000);
        if (worker.isAlive() || failure.get() != null) throw new AssertionError("Cross-thread wake", failure.get());
        FileDescriptor[] pipe = Os.pipe();
        try {
            Method descriptor = FileDescriptor.class.getDeclaredMethod("getInt$");
            descriptor.setAccessible(true);
            int fd = (Integer)descriptor.invoke(pipe[0]);
            AtomicInteger callbacks = new AtomicInteger();
            queue.addOnFileDescriptorEventListener(pipe[0], 1,
                new MessageQueue.OnFileDescriptorEventListener() {
                    public int onFileDescriptorEvents(FileDescriptor descriptor, int mask) {
                        try {
                            byte[] value = new byte[1];
                            if ((mask & 1) == 0 || Os.read(descriptor, value, 0, 1) != 1 || value[0] != 42)
                                throw new AssertionError("FD callback data");
                            callbacks.incrementAndGet();
                        } catch (Throwable problem) { failure.set(problem); }
                        return 0;
                    }
                });
            Os.write(pipe[1], new byte[] {42}, 0, 1);
            poll.invoke(queue, handle, 1000);
            if (callbacks.get() != 1 || failure.get() != null) throw new AssertionError("Public FD listener", failure.get());
            poll.invoke(queue, handle, 0);
            if (callbacks.get() != 1) throw new AssertionError("FD listener not removed");
            events.invoke(null, handle, fd, 0);
        } finally {
            Os.close(pipe[0]);
            Os.close(pipe[1]);
        }
        Method dispose = nativeMethod("dispose");
        dispose.invoke(queue);
        if (pointer.getLong(queue) != 0) throw new AssertionError("Queue not disposed");
        System.out.println("AOSP_QUEUE_JNI_OK");
    }
}
