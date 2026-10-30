package org.archtv.aospprobe;

import android.os.IBinder;
import android.os.ServiceManager;
import org.archtv.aosplinux.LocalServiceBinder;
import java.util.Collections;
import java.util.NoSuchElementException;

public final class ServiceCacheProbe {
    private static void check(boolean value,String message) {
        if (!value) throw new AssertionError(message);
    }
    private static final class Endpoint extends LocalServiceBinder {
        Endpoint() { super("org.archtv.test.LocalService"); }
    }
    public static void main(String[] args) throws Exception {
        System.load(args[0]);
        final Endpoint endpoint = new Endpoint();
        ServiceManager.initServiceCache(Collections.<String,IBinder>singletonMap("archtv.local",endpoint));
        check(ServiceManager.getService("archtv.local")==endpoint,"Original getService cache");
        check(ServiceManager.getServiceOrThrow("archtv.local")==endpoint,"Original getServiceOrThrow");
        check(ServiceManager.checkService("archtv.local")==endpoint,"Original checkService cache");
        check(endpoint.asBinder()==endpoint && endpoint.pingBinder() && endpoint.isBinderAlive(),"Live endpoint");
        check(endpoint.queryLocalInterface(endpoint.getInterfaceDescriptor())==endpoint,"Local interface identity");
        check(endpoint.queryLocalInterface("wrong")==null && endpoint.getExtension()==null,"Descriptor/extension");
        try { ServiceManager.initServiceCache(Collections.<String,IBinder>emptyMap());throw new AssertionError("Duplicate bootstrap accepted"); }
        catch (IllegalStateException expected) { }
        try { endpoint.transact(1,null,null,0);throw new AssertionError("IPC accepted"); }
        catch (UnsupportedOperationException expected) { }
        final int[] deaths={0,0};
        IBinder.DeathRecipient removed=()->deaths[0]++;
        endpoint.linkToDeath(removed,0);check(endpoint.unlinkToDeath(removed,0),"Unlink live recipient");
        try { endpoint.unlinkToDeath(removed,0);throw new AssertionError("Unknown recipient accepted"); }
        catch (NoSuchElementException expected) { }
        endpoint.linkToDeath(()->{check(!endpoint.pingBinder(),"Death callback outside live state");endpoint.close();deaths[1]++;},0);
        endpoint.close();endpoint.close();
        check(deaths[0]==0 && deaths[1]==1 && !endpoint.isBinderAlive(),"Death callback/idempotent close");
        check(endpoint.queryLocalInterface("org.archtv.test.LocalService")==null,"Closed local interface");
        try { endpoint.linkToDeath(removed,0);throw new AssertionError("Link on closed endpoint"); }
        catch (android.os.DeadObjectException expected) { }
        check(ServiceManager.getService("archtv.local")==endpoint && !endpoint.pingBinder(),"Original cache retains closed reference");
        final Endpoint callbacks = new Endpoint();
        callbacks.linkToDeath(()->{throw new IllegalArgumentException("close notification");},0);
        callbacks.linkToDeath(()->deaths[0]++,0);
        try { callbacks.close();throw new AssertionError("Callback failure swallowed"); }
        catch (IllegalArgumentException expected) { check("close notification".equals(expected.getMessage()),"Callback failure preserved"); }
        check(deaths[0]==1 && !callbacks.pingBinder(),"Remaining callbacks and closed state after callback failure");
        callbacks.close();
        check(!endpoint.unlinkToDeath(removed,0),"Unlink after close");
        if (args.length>1) {
            try {
                for (String name:new String[]{"android.view.IWindowManager","android.view.IWindowManager$Default",
                        "android.view.IWindowManager$Stub","android.view.IWindowManager$Stub$Proxy"})
                    Class.forName(name,true,ServiceCacheProbe.class.getClassLoader());
                System.out.println("WINDOW_CONTRACT_LOADED classes=4");
            } catch (LinkageError | ClassNotFoundException failure) {
                System.out.println("WINDOW_CONTRACT_BLOCKED "+failure);
                failure.printStackTrace(System.err);
            }
        }
        try { ServiceManager.getService("archtv.uncached");throw new AssertionError("Unexpected global service resolution"); }
        catch (LinkageError expected) { System.out.println("GLOBAL_SERVICE_UNAVAILABLE "+expected); }
        System.out.println("AOSP_SERVICE_CACHE_OK");
    }
}
