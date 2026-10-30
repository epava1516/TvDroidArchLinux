package org.archtv.apkruntime;

import android.graphics.Point;
import android.os.IBinder;
import android.os.ServiceManager;
import android.view.IWindowManager;
import org.archtv.aosplinux.LinuxWindowService;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.file.Paths;
import java.util.Collections;

public final class WindowServiceProbe {
    private static void check(boolean value,String message) {
        if (!value) throw new AssertionError(message);
    }
    public static void main(String[] args) throws Exception {
        System.load(args[0]);System.load(args[2]);HostProfile.initialize();
        LinuxWindowService endpoint=new LinuxWindowService(Paths.get(args[1]));
        ServiceManager.initServiceCache(Collections.<String,IBinder>singletonMap("window",endpoint));
        IWindowManager window=IWindowManager.Stub.asInterface(ServiceManager.getService("window"));
        check(window==endpoint,"Original Stub.asInterface local service identity");
        Point first=new Point();window.getBaseDisplaySize(0,first);
        System.setProperty("archtv.display.width",Integer.toString(first.x));
        System.setProperty("archtv.display.height",Integer.toString(first.y));
        java.nio.file.Files.createDirectories(Paths.get(args[5]));
        AppEnvironment.initialize(Paths.get(args[3]),Paths.get(args[5]),Paths.get(args[4]),0);
        check(AppEnvironment.current().applicationContext.getDisplayId()==0,"Actual app virtual display binding");
        android.os.Looper.prepareMainLooper();
        boolean attempted=false;
        final int[] deaths={0};endpoint.linkToDeath(()->deaths[0]++,0);
        BufferedReader input=new BufferedReader(new InputStreamReader(System.in,"UTF-8"));String line;
        while ((line=input.readLine())!=null) {
            String[] words=line.split(" +");
            if (words[0].equals("check")) {
                Point actual=new Point(),initial=new Point();window.getBaseDisplaySize(0,actual);window.getInitialDisplaySize(0,initial);
                check(actual.x==Integer.parseInt(words[1]) && actual.y==Integer.parseInt(words[2]),"Actual Wayland size");
                check(initial.x==Integer.parseInt(words[3]) && initial.y==Integer.parseInt(words[4]),"Initial Wayland size retained");
                check(window.getBaseDisplayDensity(0)==160 && window.getInitialDisplayDensity(0)==160,"Virtual display density");
                check(!window.hasNavigationBar(0) && !window.useBLAST(),"Wayland SHM backend capabilities");
                check(window.getCurrentAnimatorScale()==Float.parseFloat(words[5]),"Host animator scale policy");
                try { window.getBaseDisplaySize(1,actual);throw new AssertionError("Unknown display accepted"); }
                catch (IllegalArgumentException expected) { }
                try { window.getAnimationScales();throw new AssertionError("Unsupported window API accepted"); }
                catch (UnsupportedOperationException expected) { }
                if (!attempted) {
                    attempted=true;
                    try { new android.view.View(AppEnvironment.current().applicationContext);System.out.println("VIEW_CONSTRUCTOR_OK"); }
                    catch (LinkageError | UnsupportedOperationException | android.content.res.Resources.NotFoundException failure) {
                        System.out.println("VIEW_CONSTRUCTOR_BLOCKED "+failure);failure.printStackTrace(System.err);
                    }
                    AnimationPolicyChecks.verify(Float.parseFloat(words[5]));
                }
                System.out.println("WINDOW_SERVICE_OK "+words[1]+"x"+words[2]+" initial="+initial.x+"x"+initial.y+" scale="+words[5]);
            } else if (words[0].equals("dead")) {
                try { window.getBaseDisplaySize(0,new Point());throw new AssertionError("Dead provider served stale state"); }
                catch (android.os.DeadObjectException expected) { }
                check(!endpoint.isBinderAlive() && deaths[0]==1,"Closed endpoint after provider death");
                System.out.println("WINDOW_SERVICE_DEAD");
            } else if (words[0].equals("quit")) {
                endpoint.close();
                java.lang.reflect.Method dispose=android.os.MessageQueue.class.getDeclaredMethod("dispose");
                dispose.setAccessible(true);dispose.invoke(android.os.Looper.getMainLooper().getQueue());
                AppEnvironment.current().resources.close();
                System.out.println("WINDOW_SERVICE_CLOSED");return;
            } else throw new IllegalArgumentException("Probe command");
        }
        throw new AssertionError("Unexpected probe EOF");
    }
}
