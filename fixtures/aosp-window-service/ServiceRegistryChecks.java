package org.archtv.apkruntime;
import android.os.IBinder;
import android.os.IServiceManager;
import android.os.ServiceManager;
import android.os.ServiceDebugInfo;
import com.android.internal.os.BinderInternal;
import org.archtv.aosplinux.LinuxServiceRegistry;
import java.util.TreeMap;
public final class ServiceRegistryChecks {
    private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    public static void installAndVerify(IBinder window) throws Exception {
        try {BinderInternal.getContextObject();throw new AssertionError("Uninitialized context accepted");}
        catch(IllegalStateException expected) { }
        TreeMap<String,IBinder> services=new TreeMap<String,IBinder>();services.put("bad name",window);
        try {LinuxServiceRegistry.install(services);throw new AssertionError("Invalid registration accepted");}
        catch(IllegalArgumentException expected) { }
        services.clear();services.put("window",window);services.put("local/window",window);
        LinuxServiceRegistry registry=LinuxServiceRegistry.install(services);services.clear();
        check(BinderInternal.getContextObject()==registry,"Actual Linux native context endpoint");
        check(IServiceManager.Stub.asInterface(registry)==registry,"Original generated local interface selection");
        check(ServiceManager.getService("local/window")==window,"Original service lookup outside cache");
        check(ServiceManager.checkService("local/window")==window,"Original checkService identity");
        check(ServiceManager.getService("accessibility")==null && ServiceManager.checkService("unknown")==null,"Actual absent services");
        String[] names=ServiceManager.listServices();check(names.length==2 && names[0].equals("local/window") && names[1].equals("window"),"Actual registry listing and copied registrations");
        check(registry.listServices(IServiceManager.DUMP_FLAG_PRIORITY_HIGH).length==0,"Default registration priority filter");
        ServiceDebugInfo[] info=ServiceManager.getServiceDebugInfo();check(info.length==2 && info[0].debugPid==android.os.Binder.getCallingPid() && info[0].name.equals("local/window"),"Original debug parcelable with actual PID");
        try {registry.addService("another",window,false,8);throw new AssertionError("Mutation accepted");}
        catch(UnsupportedOperationException expected) { }
        try {registry.isDeclared("window");throw new AssertionError("Unported declaration API accepted");}
        catch(UnsupportedOperationException expected) { }
        try {LinuxServiceRegistry.install(services);throw new AssertionError("Context replacement accepted");}
        catch(IllegalStateException expected) { }
        System.out.println("LINUX_SERVICE_REGISTRY_OK services=2");
    }
    public static void verifyProviderDeath() throws Exception {
        check(ServiceManager.getService("local/window")==null,"Closed window endpoint not served by registry");
        check(ServiceManager.listServices().length==0,"Closed endpoints omitted from listing");
        LinuxServiceRegistry registry=(LinuxServiceRegistry)BinderInternal.getContextObject();registry.close();
        check(!registry.isBinderAlive(),"Registry root closes");
        try {registry.checkService("window");throw new AssertionError("Closed registry served lookup");}
        catch(android.os.DeadObjectException expected) { }
        System.out.println("LINUX_SERVICE_REGISTRY_DEAD_OK");
    }
}
