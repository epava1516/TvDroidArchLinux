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
    private static void applyLinuxBootstrapProfile(Object context) throws Exception {
        Class<?> ctx=Class.forName("android.content.Context");
        Class<?> pmType=Class.forName("android.content.pm.PackageManager");
        Class<?> ipmType=Class.forName("android.content.pm.IPackageManager");
        Object pm=call(ctx,context,"getPackageManager",new Class<?>[0]);
        Object ipm=call(Class.forName("android.app.AppGlobals"),null,"getPackageManager",new Class<?>[0]);
        int flags=pmType.getField("GET_SHARED_LIBRARY_FILES").getInt(null)
            | pmType.getField("MATCH_DIRECT_BOOT_AWARE").getInt(null)
            | pmType.getField("MATCH_DIRECT_BOOT_UNAWARE").getInt(null);
        int componentDisabled=pmType.getField("COMPONENT_ENABLED_STATE_DISABLED").getInt(null);
        int dontKill=pmType.getField("DONT_KILL_APP").getInt(null);
        StringBuilder record=new StringBuilder("SCOPE original PMS bootstrap admission, not APK compatibility or MAC authorization\n");
        try {
        java.util.List<?> persistent=(java.util.List<?>)call(Class.forName("android.content.pm.ParceledListSlice"),
            call(ipmType,ipm,"getPersistentApplications",new Class<?>[]{int.class},flags),"getList",new Class<?>[0]);
        for(Object app:persistent) {
            String name=(String)app.getClass().getField("packageName").get(app);
            int uid=app.getClass().getField("uid").getInt(app);
            String process=(String)app.getClass().getField("processName").get(app);
            record.append("PERSISTENT_BEFORE ").append(name).append(" uid=").append(uid).append(" process=").append(process).append('\n');
            // These original packages already run in the selected system process.
            // Keep SettingsProvider; do not disable the entire Settings APK for its Home component.
            boolean core=(name.equals("android") || name.equals("com.android.providers.settings"))
                && uid==1000 && "system".equals(process);
            if(!core)throw new IllegalStateException("Unselected persistent package present in actual Linux image view: "+name);
        }
        Class<?> intentType=Class.forName("android.content.Intent");
        Object home=intentType.getConstructor(String.class).newInstance("android.intent.action.MAIN");
        call(intentType,home,"addCategory",new Class<?>[]{String.class},"android.intent.category.HOME");
        Class<?> componentType=Class.forName("android.content.ComponentName");
        java.util.List<?> homes=(java.util.List<?>)call(pmType,pm,"queryIntentActivities",new Class<?>[]{intentType,int.class},home,flags);
        for(Object resolve:homes) {
            Object activity=resolve.getClass().getField("activityInfo").get(resolve);
            String pkg=(String)activity.getClass().getField("packageName").get(activity);
            String name=(String)activity.getClass().getField("name").get(activity);
            Object component=componentType.getConstructor(String.class,String.class).newInstance(pkg,name);
            call(pmType,pm,"setComponentEnabledSetting",new Class<?>[]{componentType,int.class,int.class},component,componentDisabled,dontKill);
            int actual=(Integer)call(pmType,pm,"getComponentEnabledSetting",new Class<?>[]{componentType},component);
            if(actual!=componentDisabled)throw new IllegalStateException("PMS Home state mismatch: "+pkg+"/"+name);
            record.append("HOME_COMPONENT_DISABLED ").append(pkg).append('/').append(name).append(" state=").append(actual).append('\n');
        }
        if((Boolean)call(Class.forName("android.os.SystemProperties"),null,"getBoolean",new Class<?>[]{String.class,boolean.class},"ro.system_user_home_needed",false))
            throw new IllegalStateException("Selected original profile requires Android system Home");
        java.util.List<?> remaining=(java.util.List<?>)call(Class.forName("android.content.pm.ParceledListSlice"),
            call(ipmType,ipm,"getPersistentApplications",new Class<?>[]{int.class},flags),"getList",new Class<?>[0]);
        boolean unselectedRemaining=false;
        for(Object app:remaining) {
            String name=(String)app.getClass().getField("packageName").get(app);
            int uid=app.getClass().getField("uid").getInt(app);
            String process=(String)app.getClass().getField("processName").get(app);
            if(!(name.equals("android") || name.equals("com.android.providers.settings")) || uid!=1000 || !"system".equals(process))
                unselectedRemaining=true;
            record.append("PERSISTENT_AFTER ").append(name).append(" uid=").append(uid).append(" process=").append(process).append('\n');
        }
        if(unselectedRemaining)throw new IllegalStateException("Original persistent enumeration retains disabled applications; see actual profile record");
        java.util.List<?> remainingHomes=(java.util.List<?>)call(pmType,pm,"queryIntentActivities",new Class<?>[]{intentType,int.class},home,flags);
        if(!remainingHomes.isEmpty())throw new IllegalStateException("Android Home remains enabled after original PMS profile");
        record.append("HOME_AFTER count=0\n");
        System.err.println("LINUX_BOOTSTRAP_PROFILE_ORIGINAL_PMS_READBACK_PASSED NOT_SECURITY_OR_APK_ACCEPTANCE");
        } finally {
            try(java.io.FileOutputStream output=new java.io.FileOutputStream("/data/local/tmp/archtv-mc1/linux-application-profile.txt")) {
                output.write(record.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
            } catch(java.io.IOException reportingFailure) {
                System.err.println("PROFILE_REPORT_IO_FAILURE "+reportingFailure+"\n"+record);
            }
        }
    }
    private static void verifyLinuxPlatformCapabilities(Object context) throws Exception {
        Class<?> resources=Class.forName("android.content.res.Resources");
        Object system=call(resources,null,"getSystem",new Class<?>[0]);
        Object local=call(Class.forName("android.content.Context"),context,"getResources",new Class<?>[0]);
        int id=(Integer)call(resources,system,"getIdentifier",new Class<?>[]{String.class,String.class,String.class},
            "config_enableWallpaperService","bool","android");
        if(id==0)throw new IllegalStateException("Original wallpaper platform resource missing");
        boolean systemEnabled=(Boolean)call(resources,system,"getBoolean",new Class<?>[]{int.class},id);
        boolean contextEnabled=(Boolean)call(resources,local,"getBoolean",new Class<?>[]{int.class},id);
        StringBuilder evidence=new StringBuilder("SCOPE original platform capability, not wallpaper compatibility or APK acceptance\n");
        evidence.append("WALLPAPER_RESOURCE id=").append(Integer.toHexString(id))
            .append(" system=").append(systemEnabled).append(" context=").append(contextEnabled).append('\n');
        Object assets=call(resources,system,"getAssets",new Class<?>[0]);
        Object[] apkAssets=(Object[])call(Class.forName("android.content.res.AssetManager"),assets,"getApkAssets",new Class<?>[0]);
        boolean overlayLoaded=false;
        for(Object apk:apkAssets) {
            String path=(String)call(Class.forName("android.content.res.ApkAssets"),apk,"getAssetPath",new Class<?>[0]);
            evidence.append("ASSET ").append(path).append('\n');
            overlayLoaded|=path.contains("ArchTvPlatform");
        }
        try {
            if(systemEnabled || contextEnabled || !overlayLoaded)
                throw new IllegalStateException("Actual original AssetManager did not apply Linux platform overlay: "+evidence);
            Class<?> wallpaper=Class.forName("android.app.WallpaperManager");
            Object manager=call(Class.forName("android.content.Context"),context,"getSystemService",new Class<?>[]{Class.class},wallpaper);
            boolean supported=(Boolean)call(wallpaper,manager,"isWallpaperSupported",new Class<?>[0]);
            evidence.append("WALLPAPER_ORIGINAL_MANAGER ").append(manager.getClass().getName()).append(" supported=").append(supported).append('\n');
            if(supported)throw new IllegalStateException("Wallpaper capability conflicts with missing Linux backend");
            System.err.println("LINUX_PLATFORM_OVERLAY_ORIGINAL_READBACK_PASSED NOT_WALLPAPER_COMPATIBILITY");
        } finally {
            try(java.io.FileOutputStream output=new java.io.FileOutputStream("/data/local/tmp/archtv-mc1/platform-capabilities.txt")) {
                output.write(evidence.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
            } catch(java.io.IOException failure) {System.err.println("PLATFORM_CAPABILITY_REPORT_FAILURE "+failure+"\n"+evidence);}
        }
    }
    private static void saveWaitDiagnostic(String value) {
        try (java.io.FileOutputStream output=new java.io.FileOutputStream("/data/local/tmp/archtv-mc1/selected-wait.txt")) {
            byte[] bytes=value.getBytes(java.nio.charset.StandardCharsets.UTF_8);
            output.write(bytes,0,Math.min(bytes.length,32768));
        } catch(java.io.IOException failure) { System.err.println("WAIT_DIAGNOSTIC_IO_FAILURE "+failure); }
    }
    public static void main(String[] args) {
        boolean packages = args.length==1 && args[0].equals("--packages");
        Object platformCompat=null, activityManager=null, activityTaskManager=null;

        Thread mainThread = Thread.currentThread();
        Thread diagnostic = new Thread(() -> {
            try { Thread.sleep(6000); } catch (InterruptedException stopped) { return; }
            saveWaitDiagnostic("CAPTURE_STARTED main_state="+mainThread.getState()+"\n");
            StringBuilder stack = new StringBuilder("SELECTED_MAIN_WAIT_STACK\n");
            for (StackTraceElement frame : mainThread.getStackTrace()) stack.append("    at ").append(frame).append('\n');
            System.err.println(stack.toString());
            StringBuilder savedStack=new StringBuilder(stack);saveWaitDiagnostic(savedStack.toString());
            for (java.util.Map.Entry<Thread, StackTraceElement[]> entry : Thread.getAllStackTraces().entrySet()) {
                String threadName=entry.getKey().getName();
                if (!threadName.equals("android.display") && !threadName.equals("AlarmManager")) continue;
                stack = new StringBuilder(threadName.equals("AlarmManager") ? "SELECTED_ALARM_NATIVE_WAIT_STACK\n" : "SELECTED_DISPLAY_WAIT_STACK\n");
                for (StackTraceElement frame : entry.getValue()) stack.append("    at ").append(frame).append('\n');
                System.err.println(stack.toString());
                savedStack.append(stack);saveWaitDiagnostic(savedStack.toString());
            }
        }, "selected-wait-diagnostic");
        diagnostic.setDaemon(true);
        if(!packages)diagnostic.start();
        try {
            // Keep the original fatal handler. Persist the actual asynchronous
            // framework exception before it kills this trusted process; logdw
            // can drop the crash datagram during startup bursts.
            Thread.UncaughtExceptionHandler originalFatal=Thread.getDefaultUncaughtExceptionHandler();
            if(originalFatal==null)throw new IllegalStateException("Original fatal handler absent");
            Thread.setDefaultUncaughtExceptionHandler((thread,failure) -> {
                try {
                    java.io.StringWriter text=new java.io.StringWriter();
                    text.append("ORIGINAL_ASYNC_FATAL thread=").append(thread.getName()).append('\n');
                    failure.printStackTrace(new java.io.PrintWriter(text));
                    byte[] bytes=text.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8);
                    try(java.io.FileOutputStream output=new java.io.FileOutputStream("/data/local/tmp/archtv-mc1/selected-failure.txt")) {
                        output.write(bytes,0,Math.min(bytes.length,32768));
                    }
                } catch(Throwable recordingFailure) { /* Original fatal handling still runs. */ }
                originalFatal.uncaughtException(thread,failure);
            });
            // Common original system-server IPC/scheduling setup. These calls
            // affect this trusted process, not the Linux host or tenant APKs.
            Class<?> binderInternal = Class.forName("com.android.internal.os.BinderInternal");
            call(binderInternal, null, "disableBackgroundScheduling", new Class<?>[]{boolean.class}, true);
            call(binderInternal, null, "setMaxThreads", new Class<?>[]{int.class}, 31);
            Class<?> process = Class.forName("android.os.Process");
            int priority = process.getField("THREAD_PRIORITY_FOREGROUND").getInt(null);
            call(process, null, "setThreadPriority", new Class<?>[]{int.class}, priority);
            // Establish this original Java Binder client before resource/overlay
            // initialization can make nested framework service lookups.
            if(packages) {
                Object originalManager=call(Class.forName("android.os.ServiceManager"),null,"getServiceOrThrow",
                    new Class<?>[]{String.class},"manager");
                String descriptor=(String)call(Class.forName("android.os.IBinder"),originalManager,
                    "getInterfaceDescriptor",new Class<?>[0]);
                if(!"android.os.IServiceManager".equals(descriptor))
                    throw new IllegalStateException("Unexpected original context manager: "+descriptor);
                System.err.println("ORIGINAL_JAVA_CONTEXT_MANAGER_DESCRIPTOR "+descriptor+" NOT_APK_ACCEPTANCE");
            }
            if(packages)call(Class.forName("android.database.sqlite.SQLiteCompatibilityWalFlags"),null,
                "init",new Class<?>[]{String.class},(Object)null);
            Class<?> looper = Class.forName("android.os.Looper");
            call(looper, null, "prepareMainLooper", new Class<?>[0]);
            System.loadLibrary("android_servers");
            Class<?> activityThread = Class.forName("android.app.ActivityThread");
            Object thread = call(activityThread, null, "systemMain", new Class<?>[0]);
            Object context = call(activityThread, thread, "getSystemContext", new Class<?>[0]);
            Class<?> contextType = Class.forName("android.content.Context");
            if(packages)verifyLinuxPlatformCapabilities(context);
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
            if(packages) {
                start(manager,managerType,"com.android.server.os.DeviceIdentifiersPolicyService");
                start(manager,managerType,"com.android.server.flags.FeatureFlagsService");
            }
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
                Object packagesService=call(Class.forName("com.android.server.pm.PackageManagerService"),null,"main",new Class<?>[]{contextType,installerType,domainType,boolean.class},context,installer,domain,false);
                System.err.println("PACKAGES_ORIGINAL_PMS_RETURNED REQUIRES_INSTALL_LAUNCH_VERIFICATION");
                // Original complete ART managers, after PackageManagerLocal registration.
                Class<?> dexUseType=Class.forName("com.android.server.art.DexUseManagerLocal");
                Object dexUse=call(dexUseType,null,"createInstance",new Class<?>[]{contextType},context);
                call(Class.forName("com.android.server.LocalManagerRegistry"),null,"addManager",new Class<?>[]{Class.class,Object.class},dexUseType,dexUse);


                if (Boolean.getBoolean("archtv.diagnose.wait")) diagnostic.start();
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

                // Original SystemServer publishes the registry even without a modem.
                Class<?> registryType=Class.forName("com.android.server.TelephonyRegistry");
                Class<?> registryConfig=Class.forName("com.android.server.TelephonyRegistry$ConfigurationProvider");
                Object registry=registryType.getConstructor(contextType,registryConfig).newInstance(context,registryConfig.getConstructor().newInstance());
                call(Class.forName("android.os.ServiceManager"),null,"addService",new Class<?>[]{String.class,Class.forName("android.os.IBinder")},"telephony.registry",registry);
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
                start(manager,managerType,"com.android.server.DropBoxManagerService");
                // Original SystemServer role subsystem precedes input/window policy.
                Class<?> roleHelperType=Class.forName("com.android.server.role.RoleServicePlatformHelper");
                Object roleHelper=Class.forName("com.android.server.policy.role.RoleServicePlatformHelperImpl").getConstructor(contextType).newInstance(context);
                call(Class.forName("com.android.server.LocalManagerRegistry"),null,"addManager",new Class<?>[]{Class.class,Object.class},roleHelperType,roleHelper);
                start(manager,managerType,"com.android.role.RoleService");
                // Target GSI SystemServer has folded supervision flags: its actual
                // compiled sequence starts this complete original lifecycle here.
                // Generated Flags classes are not an executable runtime API in this build.
                start(manager,managerType,"com.android.server.supervision.SupervisionService$Lifecycle");
                start(manager,managerType,"com.android.server.BatteryService");
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
                // Dispatch the original phase once to the selected coherent cohort
                // after all prerequisites. No sys.boot_completed is fabricated.
                int storagePhase=Class.forName("com.android.server.SystemService").getField("PHASE_SYSTEM_SERVICES_READY").getInt(null);

                start(manager,managerType,"com.android.server.usage.StorageStatsService$Lifecycle");
                // Original modular loader and lifecycle publish statsmanager/statscompanion.
                call(managerType,manager,"startServiceFromJar",new Class<?>[]{String.class,String.class},
                    "com.android.server.stats.StatsCompanion$Lifecycle","/apex/com.android.os.statsd/javalib/service-statsd.jar");
                start(manager,managerType,"com.android.server.UiModeManagerService");
                // Original app configuration/hibernation/ART group and order.
                start(manager,managerType,"com.android.server.locales.LocaleManagerService");
                // Pinned GSI SystemServer starts this unconditionally: build-time
                // flag optimization removed com.android.window.flags.Flags.
                // See systemserver-compiled-app-config.json; no fabricated flag API.
                start(manager,managerType,"com.android.server.appwindowlayout.AppWindowLayoutSettingsService");
                start(manager,managerType,"com.android.server.grammaticalinflection.GrammaticalInflectionService");
                start(manager,managerType,"com.android.server.apphibernation.AppHibernationService");
                call(Class.forName("com.android.server.pm.DexOptHelper"),null,"initializeArtManagerLocal",new Class<?>[]{contextType,packagesService.getClass()},context,packagesService);
                System.err.println("ORIGINAL_ART_MANAGERS_INITIALIZED NOT_ARTD_OPERATION_ACCEPTANCE");
                // Original credential/policy services before notification phase500.
                start(manager,managerType,"com.android.server.locksettings.LockSettingsService$Lifecycle");
                start(manager,managerType,"com.android.server.DeviceIdleController");
                start(manager,managerType,"com.android.server.devicepolicy.DevicePolicyManagerService$Lifecycle");
                start(manager,managerType,"com.android.server.dreams.DreamManagerService");
                // Original SystemServer network subsystem ordering. Native netd
                // and real original BPF maps must already exist; no local stub.
                Class<?> connectorType=Class.forName("android.net.ConnectivityModuleConnector");
                Object connector=call(connectorType,null,"getInstance",new Class<?>[0]);
                call(connectorType,connector,"init",new Class<?>[]{contextType},context);
                Class<?> networkStackType=Class.forName("android.net.NetworkStackClient");
                Object networkStack=call(networkStackType,null,"getInstance",new Class<?>[0]);
                call(networkStackType,networkStack,"init",new Class<?>[0]);
                Class<?> networkManagementType=Class.forName("com.android.server.net.NetworkManagementService");
                Object networkManagement=call(networkManagementType,null,"create",new Class<?>[]{contextType},context);
                Class<?> sm=Class.forName("android.os.ServiceManager");
                Class<?> ib=Class.forName("android.os.IBinder");
                call(sm,null,"addService",new Class<?>[]{String.class,ib},"network_management",networkManagement);
                start(manager,managerType,"com.android.server.NetworkScoreService$Lifecycle");
                String connectivityJar="/apex/com.android.tethering/javalib/service-connectivity.jar";
                call(managerType,manager,"startServiceFromJar",new Class<?>[]{String.class,String.class},"com.android.server.NetworkStatsServiceInitializer",connectivityJar);
                Class<?> networkPolicyType=Class.forName("com.android.server.net.NetworkPolicyManagerService");
                Object networkPolicy=networkPolicyType.getConstructor(contextType,Class.forName("android.app.IActivityManager"),Class.forName("android.os.INetworkManagementService")).newInstance(context,activityManager,networkManagement);
                call(sm,null,"addService",new Class<?>[]{String.class,ib},"netpolicy",networkPolicy);
                Object pacProxy=Class.forName("com.android.server.connectivity.PacProxyService").getConstructor(contextType).newInstance(context);
                call(sm,null,"addService",new Class<?>[]{String.class,ib},"pac_proxy",pacProxy);
                call(managerType,manager,"startServiceFromJar",new Class<?>[]{String.class,String.class},"com.android.server.ConnectivityServiceInitializer",connectivityJar);
                call(networkPolicyType,networkPolicy,"bindConnectivityManager",new Class<?>[0]);
                // Original notification/channel/storage-monitor/scheduling group.
                // AMS's FGS tracker registers a real system notification listener.
                start(manager,managerType,"com.android.server.bitmapoffload.BitmapOffloadService");
                start(manager,managerType,"com.android.server.notification.NotificationManagerService");
                Class<?> channels=Class.forName("com.android.internal.notification.SystemNotificationChannels");
                call(channels,null,"removeDeprecated",new Class<?>[]{contextType},context);
                call(channels,null,"createAll",new Class<?>[]{contextType},context);
                start(manager,managerType,"com.android.server.storage.DeviceStorageMonitorService");
                // Original SystemServer display-effects group precedes JobScheduler.
                // Phase600 NotificationManager consumes ColorDisplayManager through real Binder.
                Object displayPackageClient=call(contextType,context,"getPackageManager",new Class<?>[0]);
                boolean isWatch=(Boolean)call(Class.forName("android.content.pm.PackageManager"),displayPackageClient,
                    "hasSystemFeature",new Class<?>[]{String.class},"android.hardware.type.watch");
                if(!isWatch)start(manager,managerType,"com.android.server.twilight.TwilightService");
                start(manager,managerType,"com.android.server.display.color.ColorDisplayService");
                start(manager,managerType,"com.android.server.job.JobSchedulerService");
                // Original AMS media-session tracker requires the real session manager.
                // One existing bounded stack capture targets actual audio startup.
                if(diagnostic.getState()==Thread.State.NEW) diagnostic.start();
                start(manager,managerType,"com.android.server.audio.AudioService$Lifecycle");
                start(manager,managerType,"com.android.server.media.MediaSessionService");
                System.err.println("ORIGINAL_NETWORK_SUBSYSTEM_STARTED REQUIRES_BINDER_OPERATIONS_NOT_INTERNET_ACCEPTANCE");
                call(managerType,manager,"startBootPhase",new Class<?>[]{traceType,int.class},trace,storagePhase);
                System.err.println("ORIGINAL_SELECTED_PHASE500_RETURNED NOT_BOOT_COMPLETED_OR_APP_ACCEPTANCE");
                System.err.println("PACKAGES_ORIGINAL_USER_AMS_STORAGE_STARTED REQUIRES_INSTALL_OPERATION");
                // Original SystemServer readiness order, retaining real checks.
                call(wmType,wm,"systemReady",new Class<?>[0]);
                start(manager,managerType,"com.android.server.policy.PermissionPolicyService");
                applyLinuxBootstrapProfile(context);
                call(packagesService.getClass(),packagesService,"systemReady",new Class<?>[0]);
                // Query the exact original definition, not a shell listing of
                // permission groups (RANGING belongs to UNDEFINED).
                Object packageClient=call(contextType,context,"getPackageManager",new Class<?>[0]);
                Object rangingInfo=call(packageClient.getClass(),packageClient,"getPermissionInfo",new Class<?>[]{String.class,int.class},"android.permission.RANGING",0);
                String permissionName=(String)rangingInfo.getClass().getField("name").get(rangingInfo);
                if(!"android.permission.RANGING".equals(permissionName))throw new IllegalStateException("Original RANGING definition mismatch");
                String permissionRecord="name="+permissionName+"\npackage="+rangingInfo.getClass().getField("packageName").get(rangingInfo)+"\nprotectionLevel="+rangingInfo.getClass().getField("protectionLevel").getInt(rangingInfo)+"\n";
                try(java.io.FileOutputStream output=new java.io.FileOutputStream("/data/local/tmp/archtv-mc1/ranging-service-info.txt")) {
                    output.write(permissionRecord.getBytes(java.nio.charset.StandardCharsets.UTF_8));
                }
                call(display.getClass(),display,"systemReady",new Class<?>[]{boolean.class},false);
                Runnable linuxApplicationLoop=() -> {
                    try {
                        int activityReady=Class.forName("com.android.server.SystemService").getField("PHASE_ACTIVITY_MANAGER_READY").getInt(null);
                        call(managerType,manager,"startBootPhase",new Class<?>[]{traceType,int.class},trace,activityReady);
                        // Original SystemServer waits for original installd/PMS work before phase600.
                        call(packagesService.getClass(),packagesService,"waitForAppDataPrepared",new Class<?>[0]);
                        int appsPhase=Class.forName("com.android.server.SystemService").getField("PHASE_THIRD_PARTY_APPS_CAN_START").getInt(null);
                        call(managerType,manager,"startBootPhase",new Class<?>[]{traceType,int.class},trace,appsPhase);
                        System.err.println("LINUX_ORIGINAL_AMS_CALLBACK_RETURNING AFTER_ORIGINAL_PHASE600 NOT_BOOT_COMPLETED");
                    } catch(Exception failure) { throw new RuntimeException("Original AMS callback failed",failure); }
                };
                call(activityManager.getClass(),activityManager,"systemReady",new Class<?>[]{Runnable.class,traceType},linuxApplicationLoop,trace);
                System.err.println("LINUX_ORIGINAL_AMS_SYSTEM_READY_RETURNED NOT_BOOT_COMPLETED");
                Thread installation=new Thread(() -> {
                    try {
                        Process child=new ProcessBuilder("/system/bin/sh","-c",
                            "umask 077; /system/bin/sh /vendor/bin/install-markor.sh > /data/local/tmp/archtv-mc1/markor-install.txt 2>&1").start();
                        int result=child.waitFor();
                        System.err.println("MARKOR_ORIGINAL_SESSION_CLIENT_EXIT actual="+result+" REQUIRES_INSTALLED_BYTES");
                    } catch(Exception failure) { failure.printStackTrace(System.err); }
                },"linux-markor-installer");
                installation.start();



            }
            call(looper, null, "loop", new Class<?>[0]);
            throw new IllegalStateException("Original main looper returned unexpectedly");
        } catch (Throwable failure) {
            // Preserve the original exception even if Android's log transport is saturated.
            try {
                java.io.StringWriter text=new java.io.StringWriter();
                failure.printStackTrace(new java.io.PrintWriter(text));
                String stack=text.toString();
                try (java.io.FileOutputStream failureFile=new java.io.FileOutputStream("/data/local/tmp/archtv-mc1/selected-failure.txt")) {
                    failureFile.write(stack.substring(0,Math.min(stack.length(),32768)).getBytes("UTF-8"));
                }
            } catch (Throwable diagnosticFailure) {
                System.err.println("SELECTED_FAILURE_FILE_UNAVAILABLE "+diagnosticFailure);
            }
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
