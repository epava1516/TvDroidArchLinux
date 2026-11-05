package org.archtv.aosplinux;

import java.lang.reflect.*;
import java.util.Arrays;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Consumer;

/** Observe original ATMS snapshots. Never invent tasks, HOME or availability. */
final class TaskFocusObserver implements AutoCloseable {
    private final Object atm,listener;
    private final ArrayBlockingQueue<Boolean> changed=new ArrayBlockingQueue<>(1);
    private final AtomicBoolean closed=new AtomicBoolean();
    private final Thread worker;
    private final Consumer<int[]> publish;
    private final Runnable failure;
    private static Object call(Object receiver,String name,Class<?>[] types,Object... args) throws Exception {
        Class<?> type=receiver instanceof Class?(Class<?>)receiver:receiver.getClass();
        try{return type.getMethod(name,types).invoke(receiver instanceof Class?null:receiver,args);}
        catch(InvocationTargetException error){throw new Exception("Original "+name+" failed",error.getCause());}
    }
    TaskFocusObserver(Object atm,Consumer<int[]> publish,Runnable failure) throws Exception {
        this.atm=atm;this.publish=publish;this.failure=failure;
        // Generated subclass inherits the original complete Binder Stub and
        // all its resource/lifecycle handling. No executable SDK stubs.
        listener=Class.forName("org.archtv.aosplinux.OriginalTaskStackObserver")
            .getConstructor(Runnable.class).newInstance((Runnable)()->{if(!closed.get())changed.offer(Boolean.TRUE);});
        Class<?> type=Class.forName("android.app.ITaskStackListener");
        call(atm,"registerTaskStackListener",new Class<?>[]{type},listener);
        worker=new Thread(this::observe,"linux-original-task-state");worker.setDaemon(true);worker.start();
        changed.offer(Boolean.TRUE);
    }
    private void observe() {
        int[] previous=null;long sequence=0;
        try {
            while(!closed.get()) {
                changed.take();if(closed.get())break;
                Class<?> binder=Class.forName("android.os.Binder");
                long identity=(Long)call(binder,"clearCallingIdentity",new Class<?>[0]);
                Object info;
                try{info=call(atm,"getFocusedRootTaskInfo",new Class<?>[0]);}
                finally{call(binder,"restoreCallingIdentity",new Class<?>[]{long.class},identity);}
                int kind=0,display=-1,task=-1,activityType=0;
                if(info!=null && info.getClass().getField("topActivity").get(info)!=null) {
                    display=info.getClass().getField("displayId").getInt(info);
                    task=info.getClass().getField("taskId").getInt(info);
                    activityType=(Integer)call(info,"getActivityType",new Class<?>[0]);
                    kind=activityType==2?2:1; // Original WindowConfiguration.ACTIVITY_TYPE_HOME.
                    if(display<0 || task<0 || activityType<0 || activityType>6)throw new IllegalStateException("Original task snapshot outside contract");
                }
                int[] snapshot={kind,display,task,activityType};
                if(closed.get())break;
                if(Arrays.equals(previous,snapshot))continue;
                if(++sequence>0xffffffffL)throw new IllegalStateException("Task sequence exhausted");
                publish.accept(new int[]{0x41545232,2,(int)sequence,kind,display,task,activityType,0});
                previous=snapshot;
                System.err.println("WAYLAND_TASK_ORIGINAL_STATE seq="+sequence+" kind="+kind+" display="+display+" task="+task+" activity_type="+activityType+" NOT_APK_READINESS");
            }
        }catch(InterruptedException interrupted){if(!closed.get()){System.err.println("WAYLAND_TASK_OBSERVER_INTERRUPTED");failure.run();}}
        catch(Exception error){System.err.println("WAYLAND_TASK_OBSERVER_FAILED "+error);failure.run();}
    }
    public void close() {
        if(!closed.compareAndSet(false,true))return;
        worker.interrupt();
        try{call(atm,"unregisterTaskStackListener",new Class<?>[]{Class.forName("android.app.ITaskStackListener")},listener);}
        catch(Exception error){System.err.println("WAYLAND_TASK_UNREGISTER_FAILED "+error);}
        if(Thread.currentThread()!=worker)try{worker.join(1500);}catch(InterruptedException e){Thread.currentThread().interrupt();}
    }
}
