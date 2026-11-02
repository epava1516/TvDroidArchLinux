package org.archtv.aosplinux;

import java.lang.reflect.InvocationTargetException;

/** Linux orchestration only. All contexts, resources, services and IPC are AOSP. */
public final class SelectedServices {
    private static Object call(Class<?> type, Object receiver, String name,
                               Class<?>[] parameters, Object... arguments) throws Exception {
        try {
            return type.getMethod(name, parameters).invoke(receiver, arguments);
        } catch (InvocationTargetException failure) {
            Throwable cause = failure.getCause();
            if (cause instanceof Exception) throw (Exception) cause;
            if (cause instanceof Error) throw (Error) cause;
            throw failure;
        }
    }

    private static Object start(Object manager, Class<?> managerType, String name) throws Exception {
        return call(managerType, manager, "startService", new Class<?>[]{Class.class}, Class.forName(name));
    }
    private static void local(String name, String implementation) throws Exception {
        call(Class.forName("com.android.server.LocalServices"), null, "addService",
            new Class<?>[]{Class.class,Object.class}, Class.forName(name), Class.forName(implementation).getConstructor().newInstance());
    }
    public static void main(String[] args) {
        boolean packages = args.length==1 && args[0].equals("--packages");
        Object platformCompat=null, activityManager=null, activityTaskManager=null;

        Thread mainThread = Thread.currentThread();
        Thread diagnostic = new Thread(() -> {
            try { Thread.sleep(6000); } catch (InterruptedException stopped) { return; }
            StringBuilder stack = new StringBuilder("SELECTED_MAIN_WAIT_STACK\n");
            for (StackTraceElement frame : mainThread.getStackTrace()) stack.append("    at ").append(frame).append('\n');
            System.err.println(stack.toString());
            for (java.util.Map.Entry<Thread, StackTraceElement[]> entry : Thread.getAllStackTraces().entrySet()) {
                if (!entry.getKey().getName().equals("android.display")) continue;
                stack = new StringBuilder("SELECTED_DISPLAY_WAIT_STACK\n");
                for (StackTraceElement frame : entry.getValue()) stack.append("    at ").append(frame).append('\n');
                System.err.println(stack.toString());
            }
        }, "selected-wait-diagnostic");
        diagnostic.setDaemon(true);
        if(!packages)diagnostic.start();
        try {
            // Common original system-server IPC/scheduling setup. These calls
            // affect this trusted process, not the Linux host or tenant APKs.
            Class<?> binderInternal = Class.forName("com.android.internal.os.BinderInternal");
            call(binderInternal, null, "disableBackgroundScheduling", new Class<?>[]{boolean.class}, true);
            call(binderInternal, null, "setMaxThreads", new Class<?>[]{int.class}, 31);
            Class<?> process = Class.forName("android.os.Process");
            int priority = process.getField("THREAD_PRIORITY_FOREGROUND").getInt(null);
            call(process, null, "setThreadPriority", new Class<?>[]{int.class}, priority);
            if(packages)call(Class.forName("android.database.sqlite.SQLiteCompatibilityWalFlags"),null,
                "init",new Class<?>[]{String.class},(Object)null);
            Class<?> looper = Class.forName("android.os.Looper");
            call(looper, null, "prepareMainLooper", new Class<?>[0]);
            System.loadLibrary("android_servers");
            Class<?> activityThread = Class.forName("android.app.ActivityThread");
            Object thread = call(activityThread, null, "systemMain", new Class<?>[0]);
            Object context = call(activityThread, thread, "getSystemContext", new Class<?>[0]);
            Class<?> contextType = Class.forName("android.content.Context");
            int theme = Class.forName("com.android.internal.R$style")
                    .getField("Theme_DeviceDefault_System").getInt(null);
            call(contextType, context, "setTheme", new Class<?>[]{int.class}, theme);
            Object uiContext = call(activityThread, thread, "getSystemUiContext", new Class<?>[0]);
            call(contextType, uiContext, "setTheme", new Class<?>[]{int.class}, theme);
            if(packages) {
                // Original SystemServer creates this pool before bootstrap services.
                Class<?> pool=Class.forName("com.android.server.SystemServerInitThreadPool");
                java.lang.reflect.Method startPool=pool.getDeclaredMethod("start");
                startPool.setAccessible(true);
                startPool.invoke(null);
                Class<?> artManager=Class.forName("android.os.ArtModuleServiceManager");
                call(Class.forName("com.android.server.art.ArtModuleServiceInitializer"),null,
                    "setArtModuleServiceManager",new Class<?>[]{artManager},artManager.getConstructor().newInstance());
                System.err.println("PACKAGES_ORIGINAL_ART_MODULE_INITIALIZED NOT_ARTD_AVAILABILITY");
            }
            call(activityThread, null, "initializeMainlineModules", new Class<?>[0]);
            Class<?> managerType = Class.forName("com.android.server.SystemServiceManager");
            Object manager = managerType.getConstructor(contextType).newInstance(context);
            call(Class.forName("com.android.server.LocalServices"), null, "addService",
                    new Class<?>[]{Class.class, Object.class}, managerType, manager);
            // Original common region, required by PropertyInvalidatedCache
            // before starting services. No cache values/nonces are synthesized.
            Class<?> sharedType = Class.forName("com.android.internal.os.ApplicationSharedMemory");
            Object shared = call(sharedType, null, "create", new Class<?>[0]);
            call(sharedType, null, "setInstance", new Class<?>[]{sharedType}, shared);
            Class<?> installerType = Class.forName("com.android.server.pm.Installer");
            Object installer = call(managerType, manager, "startService", new Class<?>[]{Class.class}, installerType);
            // Real original Binder operation; default Installer is not isolated.
            // Its connection latch/remote exceptions remain intact.
            call(installerType, installer, "invalidateMounts", new Class<?>[0]);
            System.err.println("SELECTED_ORIGINAL_INSTALLER_INVALIDATE_RETURNED NOT_APK_INSTALLATION");
            if(packages) {
                Class<?> compat=Class.forName("com.android.server.compat.PlatformCompat");
                platformCompat=compat.getConstructor(contextType).newInstance(context);
                Class<?> serviceManager=Class.forName("android.os.ServiceManager");
                Class<?> binder=Class.forName("android.os.IBinder");
                call(serviceManager,null,"addService",new Class<?>[]{String.class,binder},"platform_compat",platformCompat);
                Object compatNative=Class.forName("com.android.server.compat.PlatformCompatNative").getConstructor(compat).newInstance(platformCompat);
                call(serviceManager,null,"addService",new Class<?>[]{String.class,binder},"platform_compat_native",compatNative);
                call(Class.forName("android.app.AppCompatCallbacks"),null,"install",new Class<?>[]{long[].class,long[].class,boolean.class},new long[0],new long[0],false);
                start(manager,managerType,"com.android.server.flags.FeatureFlagsService");
                start(manager,managerType,"com.android.server.uri.UriGrantsManagerService$Lifecycle");
                local("com.android.server.pm.permission.PermissionMigrationHelper","com.android.server.pm.permission.PermissionMigrationHelperImpl");
                local("com.android.server.appop.AppOpMigrationHelper","com.android.server.appop.AppOpMigrationHelperImpl");
                start(manager,managerType,"com.android.server.permission.access.AccessCheckingService");
                System.err.println("PACKAGES_ORIGINAL_ACCESS_CHECKING_STARTED NOT_PERMISSION_ACCEPTANCE");
                Object atmLifecycle=start(manager,managerType,"com.android.server.wm.ActivityTaskManagerService$Lifecycle");
                Object atm=call(atmLifecycle.getClass(),atmLifecycle,"getService",new Class<?>[0]);
                activityTaskManager=atm;
                activityManager=call(Class.forName("com.android.server.am.ActivityManagerService$Lifecycle"),null,"startService",
                    new Class<?>[]{managerType,Class.forName("com.android.server.wm.ActivityTaskManagerService")},manager,atm);
                call(activityManager.getClass(),activityManager,"setSystemServiceManager",new Class<?>[]{managerType},manager);
                call(activityManager.getClass(),activityManager,"setInstaller",new Class<?>[]{installerType},installer);
                System.err.println("PACKAGES_ORIGINAL_AMS_ATMS_STARTED NOT_APP_LAUNCH");
            }
            // Original bootstrap order: power is required by LogicalDisplayMapper.
            call(managerType, manager, "startService", new Class<?>[]{Class.class},
                    Class.forName("com.android.server.power.PowerManagerService"));
            // Original PowerManager client also requires IThermalService.
            // Preserve SystemServer's Power -> Thermal -> Display order.
            call(managerType, manager, "startService", new Class<?>[]{Class.class},
                    Class.forName("com.android.server.power.thermal.ThermalManagerService"));
            if(packages)call(activityManager.getClass(),activityManager,"initPowerManagement",new Class<?>[0]);
            // Original LightsManager is consumed by LocalDisplayAdapter.
            call(managerType, manager, "startService", new Class<?>[]{Class.class},
                    Class.forName("com.android.server.lights.LightsService"));
            Object display=call(managerType, manager, "startService", new Class<?>[]{Class.class},
                    Class.forName("com.android.server.display.DisplayManagerService"));
            Class<?> traceType = Class.forName("com.android.server.utils.TimingsTraceAndSlog");
            Object trace = traceType.getConstructor().newInstance();
            int phase = Class.forName("com.android.server.SystemService")
                    .getField("PHASE_WAIT_FOR_DEFAULT_DISPLAY").getInt(null);
            call(managerType, manager, "startBootPhase", new Class<?>[]{traceType, int.class},
                    trace, phase);
            System.err.println("SELECTED_ORIGINAL_DISPLAY_PHASE_RETURNED requires_original_IPC_verification");
            if(packages) {
                Class<?> configType=Class.forName("com.android.server.SystemConfig");
                Object config=call(configType,null,"getInstance",new Class<?>[0]);
                Class<?> domainType=Class.forName("com.android.server.pm.verify.domain.DomainVerificationService");
                Object domain=domainType.getConstructor(contextType,configType,Class.forName("com.android.server.compat.PlatformCompat")).newInstance(context,config,platformCompat);
                call(managerType,manager,"startService",new Class<?>[]{Class.forName("com.android.server.SystemService")},domain);
                call(Class.forName("com.android.server.pm.PackageManagerService"),null,"main",new Class<?>[]{contextType,installerType,domainType,boolean.class},context,installer,domain,false);
                System.err.println("PACKAGES_ORIGINAL_PMS_RETURNED REQUIRES_INSTALL_LAUNCH_VERIFICATION");
                diagnostic.start();
                // Original post-PMS ordering: publish UserManager and system AMS,
                // then bind the real storage services used by PackageInstaller.
                start(manager,managerType,"com.android.server.pm.UserManagerService$LifeCycle");
                call(Class.forName("com.android.internal.policy.AttributeCache"),null,"init",new Class<?>[]{contextType},context);
                call(activityManager.getClass(),activityManager,"setSystemProcess",new Class<?>[0]);
                call(platformCompat.getClass(),platformCompat,"registerPackageReceiver",new Class<?>[]{contextType},context);
                start(manager,managerType,"com.android.server.SystemConfigService");
                start(manager,managerType,"com.android.server.usage.UsageStatsService");
                Class<?> usageType=Class.forName("android.app.usage.UsageStatsManagerInternal");
                Object usage=call(Class.forName("com.android.server.LocalServices"),null,"getService",new Class<?>[]{Class.class},usageType);
                call(activityManager.getClass(),activityManager,"setUsageStatsManager",new Class<?>[]{usageType},usage);

                start(manager,managerType,"com.android.server.accounts.AccountManagerService$Lifecycle");
                start(manager,managerType,"com.android.server.content.ContentService$Lifecycle");
                Object providers=call(activityManager.getClass(),activityManager,"getContentProviderHelper",new Class<?>[0]);
                call(providers.getClass(),providers,"installSystemProviders",new Class<?>[0]);
                start(manager,managerType,"com.android.server.deviceconfig.DeviceConfigInit$Lifecycle");
                call(Class.forName("android.database.sqlite.SQLiteCompatibilityWalFlags"),null,"reset",new Class<?>[0]);
                System.err.println("PACKAGES_ORIGINAL_SYSTEM_PROVIDERS_INSTALLED REQUIRES_PROVIDER_OPERATION");
                Class<?> resourcesType=Class.forName("com.android.server.resources.ResourcesManagerService");
                Object resources=resourcesType.getConstructor(contextType).newInstance(context);
                call(resourcesType,resources,"setActivityManagerService",new Class<?>[]{activityManager.getClass()},activityManager);
                call(managerType,manager,"startService",new Class<?>[]{Class.forName("com.android.server.SystemService")},resources);
                // Original SystemServer role subsystem precedes input/window policy.
                Class<?> roleHelperType=Class.forName("com.android.server.role.RoleServicePlatformHelper");
                Object roleHelper=Class.forName("com.android.server.policy.role.RoleServicePlatformHelperImpl").getConstructor(contextType).newInstance(context);
                call(Class.forName("com.android.server.LocalManagerRegistry"),null,"addManager",new Class<?>[]{Class.class,Object.class},roleHelperType,roleHelper);
                start(manager,managerType,"com.android.role.RoleService");
                start(manager,managerType,"com.android.server.sensorprivacy.SensorPrivacyService");
                start(manager,managerType,"com.android.server.sensors.SensorService");
                start(manager,managerType,"com.android.server.alarm.AlarmManagerService");
                Object inputLifecycle=start(manager,managerType,"com.android.server.input.InputManagerService$Lifecycle");
                Object input=call(inputLifecycle.getClass(),inputLifecycle,"getService",new Class<?>[0]);
                start(manager,managerType,"com.android.server.devicestate.DeviceStateManagerService");
                int sensorPhase=Class.forName("com.android.server.SystemService").getField("PHASE_WAIT_FOR_SENSOR_SERVICE").getInt(null);
                call(managerType,manager,"startBootPhase",new Class<?>[]{traceType,int.class},trace,sensorPhase);
                Class<?> wmType=Class.forName("com.android.server.wm.WindowManagerService");
                Class<?> policyType=Class.forName("com.android.server.policy.WindowManagerPolicy");
                Object policy=Class.forName("com.android.server.policy.PhoneWindowManager").getConstructor().newInstance();
                Object wm=call(wmType,null,"main",new Class<?>[]{contextType,input.getClass(),boolean.class,policyType,activityTaskManager.getClass()},context,input,false,policy,activityTaskManager);
                Class<?> serviceManager=Class.forName("android.os.ServiceManager");
                Class<?> binder=Class.forName("android.os.IBinder");
                Class<?> smInterface=Class.forName("android.os.IServiceManager");
                int dumpFlags=smInterface.getField("DUMP_FLAG_PRIORITY_CRITICAL").getInt(null)|smInterface.getField("DUMP_FLAG_PRIORITY_HIGH").getInt(null)|smInterface.getField("DUMP_FLAG_PROTO").getInt(null);
                call(serviceManager,null,"addService",new Class<?>[]{String.class,binder,boolean.class,int.class},"window",wm,false,dumpFlags);
                call(activityManager.getClass(),activityManager,"setWindowManager",new Class<?>[]{wmType},wm);
                call(wmType,wm,"onInitReady",new Class<?>[0]);
                Object inputCallback=call(wmType,wm,"getInputManagerCallback",new Class<?>[0]);
                call(input.getClass(),input,"setWindowManagerCallbacks",new Class<?>[]{Class.forName("com.android.server.input.InputManagerService$WindowManagerCallbacks")},inputCallback);
                call(input.getClass(),input,"start",new Class<?>[0]);
                call(display.getClass(),display,"windowManagerAndInputReady",new Class<?>[0]);
                call(wmType,wm,"displayReady",new Class<?>[0]);
                System.err.println("MARKOR_ORIGINAL_WMS_INPUT_STARTED REQUIRES_APP_SURFACE_AND_INPUT");

                Object storageLifecycle=start(manager,managerType,"com.android.server.StorageManagerService$Lifecycle");
                Class<?> pmInternalType=Class.forName("android.content.pm.PackageManagerInternal");
                Object pmInternal=call(Class.forName("com.android.server.LocalServices"),null,"getService",new Class<?>[]{Class.class},pmInternalType);
                if(pmInternal==null)throw new IllegalStateException("Original PackageManagerInternal absent");
                for(String dependency:new String[]{"package","appops"}) {
                    if(call(Class.forName("android.os.ServiceManager"),null,"checkService",new Class<?>[]{String.class},dependency)==null)
                        throw new IllegalStateException("Original storage dependency absent: "+dependency);
                }
                // Linux dispatches this original subsystem callback after its
                // actual dependencies. This is not a global Android boot phase.
                int storagePhase=Class.forName("com.android.server.SystemService").getField("PHASE_SYSTEM_SERVICES_READY").getInt(null);
                call(storageLifecycle.getClass(),storageLifecycle,"onBootPhase",new Class<?>[]{int.class},storagePhase);

                start(manager,managerType,"com.android.server.usage.StorageStatsService$Lifecycle");
                System.err.println("PACKAGES_ORIGINAL_USER_AMS_STORAGE_STARTED REQUIRES_INSTALL_OPERATION");
                // Run the real PackageInstaller client after dependency/lifecycle
                // completion, while the original main looper can process work.
                Thread installation=new Thread(() -> {
                    try {
                        Process child=new ProcessBuilder("/system/bin/sh","-c",
                            "umask 077; /system/bin/sh /vendor/bin/install-markor.sh > /data/local/tmp/archtv-mc1/markor-install.txt 2>&1").start();
                        int result=child.waitFor();
                        System.err.println("MARKOR_ORIGINAL_SESSION_CLIENT_EXIT actual="+result+" REQUIRES_INSTALLED_BYTES");
                    } catch(Exception failure) {
                        failure.printStackTrace(System.err);
                    }
                },"linux-markor-installer");
                installation.start();


            }
            call(looper, null, "loop", new Class<?>[0]);
            throw new IllegalStateException("Original main looper returned unexpectedly");
        } catch (Throwable failure) {
            Throwable cause=failure;
            for(int depth=0;cause!=null && depth<8;depth++,cause=cause.getCause()) {
                String message=String.valueOf(cause.getMessage());
                if(message.length()>700)message=message.substring(0,700);
                System.err.println("SELECTED_FAILURE_CAUSE depth="+depth+" type="+cause.getClass().getName()+" message="+message);
            }
            failure.printStackTrace(System.err);
            System.exit(1);
        }
    }
}
