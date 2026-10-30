package org.archtv.apkruntime;
import java.io.File;
import java.lang.reflect.*;
/** Original framework bootstrap attempt. No substitute android.* classes or skipped attach calls. */
public final class OriginalBootstrapProbe {
    private static String stage="native-libraries";
    private static void step(String name){stage=name;System.out.println("BOOTSTRAP_STAGE "+name);}
    public static void main(String[] args) {
        try {
            step("native-libraries");System.load("/native/linux.so");System.load("/native/resources.so");System.load("/native/binder.so");
            HostProfile.initialize();
            if(android.os.Process.myUid()!=10000 || android.os.Binder.getCallingUid()!=10000)throw new AssertionError("Actual namespace UID must be non-system");
            System.out.println("BOOTSTRAP_ACTUAL_UID_OK 10000");
            org.archtv.aosplinux.LinuxServiceRegistry.install(java.util.Collections.<String,android.os.IBinder>emptyMap());
            step("main-looper");android.os.Looper.prepareMainLooper();
            step("activity-thread");Class<?> threadType=Class.forName("android.app.ActivityThread");Constructor<?> ctor=threadType.getDeclaredConstructor();ctor.setAccessible(true);Object thread=ctor.newInstance();
            step("system-context");threadType.getMethod("getSystemContext").invoke(thread);
            step("parse-original-package");Class<?> parserType=Class.forName("android.content.pm.PackageParser");Object parser=parserType.getDeclaredConstructor().newInstance();Object pkg=parserType.getMethod("parsePackage",File.class,int.class).invoke(parser,new File("/app/app.apk"),0);
            android.content.pm.ApplicationInfo info=(android.content.pm.ApplicationInfo)pkg.getClass().getField("applicationInfo").get(pkg);
            if(!"net.gsantner.markor".equals(info.packageName) || !args[0].equals(info.className))throw new AssertionError("Original manifest metadata differs");
            info.uid=android.os.Process.myUid();info.dataDir="/data/app";
            step("loaded-apk");Class<?> compatType=Class.forName("android.content.res.CompatibilityInfo");Object compat=compatType.getField("DEFAULT_COMPATIBILITY_INFO").get(null);Object loaded=threadType.getMethod("getPackageInfoNoCheck",android.content.pm.ApplicationInfo.class,compatType).invoke(thread,info,compat);
            step("application-context");Class<?> contextType=Class.forName("android.app.ContextImpl");Method create=contextType.getDeclaredMethod("createAppContext",threadType,Class.forName("android.app.LoadedApk"));create.setAccessible(true);Object context=create.invoke(null,thread,loaded);
            step("original-application-attach");Object instrumentation=Class.forName("android.app.Instrumentation").getDeclaredConstructor().newInstance();Object app=instrumentation.getClass().getMethod("newApplication",ClassLoader.class,String.class,android.content.Context.class).invoke(instrumentation,OriginalBootstrapProbe.class.getClassLoader(),info.className,context);
            step("application-oncreate");instrumentation.getClass().getMethod("callApplicationOnCreate",android.app.Application.class).invoke(instrumentation,app);
            System.out.println("APPLICATION_ONCREATE_OK "+app.getClass().getName());
        } catch(Throwable failure) {
            while(failure instanceof InvocationTargetException && failure.getCause()!=null)failure=failure.getCause();
            System.err.println("BOOTSTRAP_BLOCKED stage="+stage+" "+failure);failure.printStackTrace(System.err);System.exit(2);
        }
    }
}
