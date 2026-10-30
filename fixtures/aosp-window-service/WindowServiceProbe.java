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
        String renderNodeLibrary=System.getProperty("archtv.rendernode.library");
        if(renderNodeLibrary!=null)System.load(renderNodeLibrary);
        String binderHolder=System.getProperty("archtv.binder.holder.library");
        if(binderHolder!=null) {
            System.load(binderHolder);
            java.lang.reflect.Field field=android.os.Binder.class.getDeclaredField("mObject");field.setAccessible(true);
            java.util.HashSet<Long> holders=new java.util.HashSet<Long>();
            android.os.Binder[] tokens=new android.os.Binder[32];
            for(int i=0;i<tokens.length;i++) {
                tokens[i]=new android.os.Binder("org.archtv.token."+i);
                check(field.getLong(tokens[i])!=0 && holders.add(field.getLong(tokens[i])),"Independent original Binder holder");
                final android.os.Binder token=tokens[i];android.os.IInterface owner=()->token;
                token.attachInterface(owner,"org.archtv.local."+i);
                check(token.queryLocalInterface("org.archtv.local."+i)==owner,"Original local interface identity");
                check(token.queryLocalInterface("wrong")==null && token.isBinderAlive() && token.pingBinder(),"Original local token behavior");
            }
            try { tokens[0].getExtension();throw new AssertionError("Unported Binder extension accepted"); }
            catch(UnsatisfiedLinkError expected) { }
            System.out.println("BINDER_HOLDER_ART_OK objects=32");
        }
        LinuxWindowService endpoint=new LinuxWindowService(Paths.get(args[1]));
        ServiceManager.initServiceCache(Collections.<String,IBinder>singletonMap("window",endpoint));
        if(Boolean.getBoolean("archtv.service.registry"))
            Class.forName("org.archtv.apkruntime.ServiceRegistryChecks").getMethod("installAndVerify",IBinder.class).invoke(null,endpoint);
        IWindowManager window=IWindowManager.Stub.asInterface(ServiceManager.getService("window"));
        check(window==endpoint,"Original Stub.asInterface local service identity");
        Point first=new Point();window.getBaseDisplaySize(0,first);
        System.setProperty("archtv.display.width",Integer.toString(first.x));
        System.setProperty("archtv.display.height",Integer.toString(first.y));
        java.nio.file.Files.createDirectories(Paths.get(args[5]));
        AppEnvironment.initialize(Paths.get(args[3]),Paths.get(args[5]),Paths.get(args[4]),0);
        check(AppEnvironment.current().applicationContext.getDisplayId()==0,"Actual app virtual display binding");
        android.os.Looper.prepareMainLooper();
        android.content.Context app=AppEnvironment.current().applicationContext;
        for(String permission:new String[]{"android.permission.INTERACT_ACROSS_USERS","android.permission.INTERACT_ACROSS_USERS_FULL","android.permission.INTERNET","org.archtv.UNKNOWN"})
            check(app.checkCallingOrSelfPermission(permission)==-1,"No Android permission grants: "+permission);
        try { app.checkCallingOrSelfPermission(null);throw new AssertionError("Null permission accepted"); }
        catch(IllegalArgumentException expected) { }
        System.out.println("LINUX_PERMISSION_QUERY_OK grants=0");
        boolean attempted=false;
        android.view.View layoutView=null;final int[] layoutCallbacks={0};
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
                    try {
                        android.view.View view=new android.view.View(AppEnvironment.current().applicationContext);
                        check(view.getClass()==android.view.View.class,"Original View instance");
                        check(view.getContext()==AppEnvironment.current().applicationContext,"Original context retained");
                        check(view.getWidth()==0 && view.getHeight()==0,"Unlaid View dimensions");
                        check(view.getId()==android.view.View.NO_ID && view.getParent()==null,"Unattached View state");
                        check(view.getVisibility()==android.view.View.VISIBLE && view.getAlpha()==1.0f,"Initial visibility and native alpha");
                        check(!android.graphics.drawable.GradientDrawable.sWrapNegativeAngleMeasurements,"Actual APK target 28 compatibility");
                        System.out.println("VIEW_CONSTRUCTOR_OK");System.out.println("VIEW_BASE_STATE_OK");
                        try {
                            view.measure(android.view.View.MeasureSpec.makeMeasureSpec(320,android.view.View.MeasureSpec.EXACTLY),
                                    android.view.View.MeasureSpec.makeMeasureSpec(180,android.view.View.MeasureSpec.EXACTLY));
                            check(view.getMeasuredWidth()==320 && view.getMeasuredHeight()==180,"Exact original View measure");
                            view.measure(android.view.View.MeasureSpec.makeMeasureSpec(210,android.view.View.MeasureSpec.AT_MOST),
                                    android.view.View.MeasureSpec.makeMeasureSpec(110,android.view.View.MeasureSpec.AT_MOST));
                            check(view.getMeasuredWidth()==210 && view.getMeasuredHeight()==110,"Base View AT_MOST uses available size");
                            view.measure(android.view.View.MeasureSpec.makeMeasureSpec(0,android.view.View.MeasureSpec.UNSPECIFIED),
                                    android.view.View.MeasureSpec.makeMeasureSpec(0,android.view.View.MeasureSpec.UNSPECIFIED));
                            check(view.getMeasuredWidth()==0 && view.getMeasuredHeight()==0,"Unspecified empty View size");
                            view.setMinimumWidth(96);view.setMinimumHeight(54);
                            view.measure(android.view.View.MeasureSpec.makeMeasureSpec(0,android.view.View.MeasureSpec.UNSPECIFIED),
                                    android.view.View.MeasureSpec.makeMeasureSpec(0,android.view.View.MeasureSpec.UNSPECIFIED));
                            check(view.getMeasuredWidth()==96 && view.getMeasuredHeight()==54,"Original suggested minimum dimensions");
                            view.measure(android.view.View.MeasureSpec.makeMeasureSpec(320,android.view.View.MeasureSpec.EXACTLY),
                                    android.view.View.MeasureSpec.makeMeasureSpec(180,android.view.View.MeasureSpec.EXACTLY));
                            check(view.getMeasuredWidth()==320 && view.getMeasuredHeight()==180,"Exact dimensions after minimum/spec changes");
                            System.out.println("VIEW_MEASURE_OK cases=5");
                            view.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,or,ob)->layoutCallbacks[0]++);
                            view.layout(13,17,333,197);
                            check(view.getLeft()==13 && view.getTop()==17 && view.getRight()==333 && view.getBottom()==197,"Original layout coordinates");
                            check(view.getWidth()==320 && view.getHeight()==180 && view.isLaidOut(),"Original layout dimensions/state");
                            check(layoutCallbacks[0]==1,"Original layout change notification");
                            layoutView=view;
                            System.out.println("VIEW_LAYOUT_OK");
                        } catch (LinkageError | UnsupportedOperationException | android.content.res.Resources.NotFoundException failure) {
                            System.out.println("VIEW_LAYOUT_BLOCKED "+failure);failure.printStackTrace(System.err);
                        }
                    }
                    catch (LinkageError | UnsupportedOperationException | android.content.res.Resources.NotFoundException failure) {
                        System.out.println("VIEW_CONSTRUCTOR_BLOCKED "+failure);failure.printStackTrace(System.err);
                    }
                    AnimationPolicyChecks.verify(Float.parseFloat(words[5]));
                }
                if(layoutView!=null) {
                    layoutView.measure(android.view.View.MeasureSpec.makeMeasureSpec(actual.x,android.view.View.MeasureSpec.EXACTLY),
                            android.view.View.MeasureSpec.makeMeasureSpec(actual.y,android.view.View.MeasureSpec.EXACTLY));
                    layoutView.layout(0,0,actual.x,actual.y);
                    check(layoutView.getWidth()==actual.x && layoutView.getHeight()==actual.y,"Original View follows actual window dimensions");
                    java.lang.reflect.Field field=android.view.View.class.getDeclaredField("mRenderNode");field.setAccessible(true);
                    android.graphics.RenderNode node=(android.graphics.RenderNode)field.get(layoutView);
                    check(node.getLeft()==0 && node.getTop()==0 && node.getRight()==actual.x && node.getBottom()==actual.y,"Original native RenderNode bounds follow layout");
                    check(node.getWidth()==actual.x && node.getHeight()==actual.y,"Native RenderNode dimensions");
                    int callbacks=layoutCallbacks[0];layoutView.layout(0,0,actual.x,actual.y);
                    check(layoutCallbacks[0]==callbacks,"Unchanged layout does not notify listeners");
                    System.out.println("VIEW_LAYOUT_RESIZE_OK "+actual.x+"x"+actual.y);
                }
                System.out.println("WINDOW_SERVICE_OK "+words[1]+"x"+words[2]+" initial="+initial.x+"x"+initial.y+" scale="+words[5]);
            } else if (words[0].equals("dead")) {
                try { window.getBaseDisplaySize(0,new Point());throw new AssertionError("Dead provider served stale state"); }
                catch (android.os.DeadObjectException expected) { }
                check(!endpoint.isBinderAlive() && deaths[0]==1,"Closed endpoint after provider death");
                if(Boolean.getBoolean("archtv.service.registry"))
                    Class.forName("org.archtv.apkruntime.ServiceRegistryChecks").getMethod("verifyProviderDeath").invoke(null);
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
