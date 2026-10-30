package org.archtv.aosplinux;

import android.os.IBinder;
import android.os.IServiceManager;
import android.os.IServiceCallback;
import android.os.IClientCallback;
import android.os.ServiceDebugInfo;
import android.os.ConnectionInfo;
import android.os.DeadObjectException;
import java.util.Map;
import java.util.TreeMap;
import java.util.ArrayList;

/** Immutable, process-local service registry. No Android servicemanager daemon or Binder IPC. */
public final class LinuxServiceRegistry extends LocalServiceBinder implements IServiceManager {
    private static LinuxServiceRegistry context;
    private final TreeMap<String,IBinder> services=new TreeMap<String,IBinder>();
    private final int ownerPid=android.os.Binder.getCallingPid();
    private LinuxServiceRegistry(Map<String,IBinder> registrations) {
        super("android.os.IServiceManager");
        if(registrations==null || registrations.size()>128)throw new IllegalArgumentException("Invalid local registrations");
        for(Map.Entry<String,IBinder> entry:registrations.entrySet()) {
            validName(entry.getKey());IBinder binder=entry.getValue();
            if(!(binder instanceof LocalServiceBinder || binder instanceof android.os.Binder) || !binder.isBinderAlive())
                throw new IllegalArgumentException("Only live local service endpoints are supported");
            services.put(entry.getKey(),binder);
        }
    }
    public static synchronized LinuxServiceRegistry install(Map<String,IBinder> registrations) {
        if(context!=null)throw new IllegalStateException("Local service context already installed");
        context=new LinuxServiceRegistry(registrations);return context;
    }
    /** Called by the Linux JNI implementation of BinderInternal.getContextObject. */
    public static synchronized IBinder contextObject() {
        if(context==null)throw new IllegalStateException("Local service context is not installed");
        return context;
    }
    private static void validName(String name) {
        if(name==null || !name.matches("[A-Za-z0-9_.:/-]{1,127}"))throw new IllegalArgumentException("Invalid local service name");
    }
    private void live() throws DeadObjectException {
        if(!isBinderAlive())throw new DeadObjectException();
    }
    @Override public synchronized IBinder checkService(String name) throws DeadObjectException {
        live();validName(name);IBinder endpoint=services.get(name);
        return endpoint!=null && endpoint.isBinderAlive()?endpoint:null;
    }
    @Override public IBinder getService(String name) throws DeadObjectException { return checkService(name); }
    @Override public synchronized String[] listServices(int priority) throws DeadObjectException {
        live();if((priority & ~(IServiceManager.DUMP_FLAG_PRIORITY_ALL|IServiceManager.DUMP_FLAG_PROTO))!=0)throw new IllegalArgumentException("Unknown dump priority");
        ArrayList<String> result=new ArrayList<String>();
        if((priority&IServiceManager.DUMP_FLAG_PRIORITY_DEFAULT)!=0)
            for(String name:services.keySet())if(services.get(name).isBinderAlive())result.add(name);
        return result.toArray(new String[result.size()]);
    }
    @Override public synchronized ServiceDebugInfo[] getServiceDebugInfo() throws DeadObjectException {
        live();ArrayList<ServiceDebugInfo> result=new ArrayList<ServiceDebugInfo>();
        for(String name:services.keySet())if(services.get(name).isBinderAlive()) {
            ServiceDebugInfo info=new ServiceDebugInfo();info.name=name;info.debugPid=ownerPid;result.add(info);
        }
        return result.toArray(new ServiceDebugInfo[result.size()]);
    }
    private static UnsupportedOperationException unsupported(String name) {return new UnsupportedOperationException("Unsupported local service registry API: "+name);}
    @Override public void addService(String name,IBinder service,boolean isolated,int priority) {throw unsupported("addService");}
    @Override public void registerForNotifications(String name,IServiceCallback callback) {throw unsupported("registerForNotifications");}
    @Override public void unregisterForNotifications(String name,IServiceCallback callback) {throw unsupported("unregisterForNotifications");}
    @Override public boolean isDeclared(String name) {throw unsupported("isDeclared");}
    @Override public String[] getDeclaredInstances(String iface) {throw unsupported("getDeclaredInstances");}
    @Override public String updatableViaApex(String name) {throw unsupported("updatableViaApex");}
    @Override public ConnectionInfo getConnectionInfo(String name) {throw unsupported("getConnectionInfo");}
    @Override public void registerClientCallback(String name,IBinder service,IClientCallback callback) {throw unsupported("registerClientCallback");}
    @Override public void tryUnregisterService(String name,IBinder service) {throw unsupported("tryUnregisterService");}
}
