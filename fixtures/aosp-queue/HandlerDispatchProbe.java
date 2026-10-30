package org.archtv.aospprobe;

import android.os.Handler;
import android.os.Looper;

/** Next gate: actual original Handler/Looper dispatch, not direct native reflection. */
public final class HandlerDispatchProbe {
    public static void main(String[] args) {
        System.load(args[0]);
        Looper.prepare();
        Handler handler = new Handler(Looper.myLooper());
        handler.post(new Runnable() {
            public void run() {
                System.out.println("AOSP_HANDLER_DISPATCHED");
                Looper.myLooper().quit();
            }
        });
        Looper.loop();
    }
}
