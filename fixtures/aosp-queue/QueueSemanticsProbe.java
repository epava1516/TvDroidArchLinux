package org.archtv.aospprobe;

import android.os.Handler;
import android.os.Looper;
import android.os.MessageQueue;
import android.os.SystemClock;
import android.os.ThreadLocalWorkSource;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

/** Behavioral checks against original Java scheduling, not the native backend alone. */
public final class QueueSemanticsProbe {
    private interface Setup { void run(Handler handler) throws Exception; }
    private static final class Worker {
        final AtomicReference<Throwable> failure = new AtomicReference<Throwable>();
        final CountDownLatch ready = new CountDownLatch(1);
        volatile Handler handler;
        final Thread thread;
        Worker(Setup setup) throws Exception {
            thread = new Thread(new Runnable() {
                public void run() {
                    try {
                        Looper.prepare();
                        handler = new Handler(Looper.myLooper());
                        setup.run(handler);
                        ready.countDown();
                        Looper.loop();
                        if (ThreadLocalWorkSource.getUid() != ThreadLocalWorkSource.UID_NONE)
                            throw new AssertionError("WorkSource leaked after dispatch");
                    } catch (Throwable problem) { failure.set(problem); }
                    finally { ready.countDown(); }
                }
            });
            // Each successful scenario joins its worker. A failed assertion must
            // still let the test process report failure instead of hanging forever.
            thread.setDaemon(true);
            thread.start();
            if (!ready.await(8, TimeUnit.SECONDS)) throw new AssertionError("Worker startup timed out");
            if (failure.get() != null) throw new AssertionError("Worker setup failed", failure.get());
        }
        void finish() throws Exception {
            thread.join(8000);
            if (thread.isAlive()) {
                handler.getLooper().quit();
                thread.join(2000);
                throw new AssertionError("Worker did not finish");
            }
            if (failure.get() != null) throw new AssertionError("Worker failed", failure.get());
        }
    }
    public static void main(String[] args) throws Exception {
        System.load(args[0]);
        System.out.println("QUEUE_STAGE ordered");
        List<String> order = new ArrayList<String>();
        int[] idle = new int[1];
        Worker ordered = new Worker(new Setup() {
            public void run(Handler handler) {
                MessageQueue queue = Looper.myQueue();
                queue.addIdleHandler(new MessageQueue.IdleHandler() {
                    public boolean queueIdle() { idle[0]++; return false; }
                });
                long token = ThreadLocalWorkSource.setUid(1234);
                handler.post(new Runnable() {
                    public void run() {
                        if (ThreadLocalWorkSource.getUid() != 1234) throw new AssertionError("WorkSource not propagated");
                        order.add("first");
                    }
                });
                ThreadLocalWorkSource.restore(token);
                handler.post(new Runnable() { public void run() { order.add("second"); } });
                Runnable cancelled = new Runnable() { public void run() { throw new AssertionError("Cancelled callback ran"); } };
                handler.postDelayed(cancelled, 50);
                handler.removeCallbacks(cancelled);
                long scheduled = SystemClock.uptimeMillis();
                handler.postDelayed(new Runnable() {
                    public void run() {
                        if (SystemClock.uptimeMillis() < scheduled+100) throw new AssertionError("Early delayed message");
                        if (idle[0] != 1) throw new AssertionError("Idle handler count: "+idle[0]);
                        order.add("delayed");
                        Looper.myLooper().quit();
                    }
                }, 100);
            }
        });
        ordered.finish();
        if (!order.equals(Arrays.asList("first", "second", "delayed"))) throw new AssertionError("Message order: "+order);
        System.out.println("QUEUE_STAGE cross-thread");
        Worker cross = new Worker(new Setup() { public void run(Handler handler) { } });
        long deadline = System.nanoTime()+5000000000L;
        while (!cross.handler.getLooper().getQueue().isPolling() && System.nanoTime() < deadline) Thread.sleep(1);
        if (!cross.handler.getLooper().getQueue().isPolling()) throw new AssertionError("Worker not polling");
        long token = ThreadLocalWorkSource.setUid(77);
        cross.handler.post(new Runnable() {
            public void run() {
                if (Thread.currentThread() != cross.thread || ThreadLocalWorkSource.getUid() != 77)
                    throw new AssertionError("Cross-thread delivery");
                Looper.myLooper().quit();
            }
        });
        ThreadLocalWorkSource.restore(token);
        cross.finish();
        System.out.println("QUEUE_STAGE barrier");
        List<String> barrierOrder = new ArrayList<String>();
        Worker barrier = new Worker(new Setup() {
            public void run(Handler handler) throws Exception {
                MessageQueue queue = Looper.myQueue();
                Method post = MessageQueue.class.getDeclaredMethod("postSyncBarrier"); post.setAccessible(true);
                Method remove = MessageQueue.class.getDeclaredMethod("removeSyncBarrier", int.class); remove.setAccessible(true);
                int barrierToken = (Integer)post.invoke(queue);
                handler.post(new Runnable() { public void run() { barrierOrder.add("sync"); Looper.myLooper().quit(); } });
                Handler.createAsync(Looper.myLooper()).post(new Runnable() {
                    public void run() {
                        barrierOrder.add("async");
                        try { remove.invoke(queue, barrierToken); } catch (Exception failure) { throw new AssertionError(failure); }
                    }
                });
            }
        });
        barrier.finish();
        if (!barrierOrder.equals(Arrays.asList("async", "sync"))) throw new AssertionError("Barrier order: "+barrierOrder);
        System.out.println("QUEUE_STAGE quitSafely");
        int[] safeCount = new int[1];
        Worker safe = new Worker(new Setup() {
            public void run(Handler handler) {
                handler.post(new Runnable() { public void run() { safeCount[0]++; } });
                handler.postDelayed(new Runnable() { public void run() { throw new AssertionError("Future message after quitSafely"); } }, 60000);
                Looper.myLooper().quitSafely();
            }
        });
        safe.finish();
        if (safeCount[0] != 1) throw new AssertionError("quitSafely lost due message");
        System.out.println("QUEUE_STAGE quit");
        Worker immediate = new Worker(new Setup() {
            public void run(Handler handler) {
                handler.post(new Runnable() { public void run() { throw new AssertionError("Message after immediate quit"); } });
                Looper.myLooper().quit();
            }
        });
        immediate.finish();
        System.out.println("AOSP_QUEUE_SEMANTICS_OK");
    }
}
