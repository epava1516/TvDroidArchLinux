package org.archtv.apkruntime;

import android.content.pm.ApplicationInfo;
import java.nio.file.Paths;

public final class MetadataProbe {
    private static void check(boolean value,String message) {
        if(!value)throw new AssertionError(message);
    }
    public static void main(String[] args) throws Exception {
        System.load(args[0]);System.load(args[1]);HostProfile.initialize();
        AppEnvironment.initialize(Paths.get(args[2]),Paths.get(args[3]));
        android.content.Context context=AppEnvironment.current().applicationContext;
        ApplicationInfo info=context.getApplicationInfo();
        check(info.getClass()==ApplicationInfo.class,"Original ApplicationInfo class");
        check(info.packageName.equals(args[4]) && context.getPackageName().equals(args[4]),"Actual manifest package");
        check(info.minSdkVersion==21 && info.targetSdkVersion==Integer.parseInt(args[5]),"Actual uses-sdk");
        check(info.uid==android.os.Binder.getCallingUid(),"Actual Linux UID");
        check(info.sourceDir.equals(Paths.get(args[2]).toAbsolutePath().normalize().toString())
                && info.sourceDir.equals(info.publicSourceDir),"APK source path");
        check(info.dataDir.equals(Paths.get(args[3]).toAbsolutePath().normalize().toString()),"Linux data path");
        check(info.createTimestamp>0,"Original constructor uses real clock");
        if(args[4].equals("org.archtv.metadata")) {
            check((info.flags&ApplicationInfo.FLAG_HAS_CODE)==0,"Literal hasCode=false");
            check((info.flags&ApplicationInfo.FLAG_DEBUGGABLE)!=0,"Literal debuggable=true");
            check((info.flags&ApplicationInfo.FLAG_HARDWARE_ACCELERATED)==0,"Literal hardware=false");
            check((info.flags&ApplicationInfo.FLAG_SUPPORTS_RTL)!=0,"Literal RTL=true");
            check(info.processName.equals("org.archtv.metadata:metadata"),"Private process declaration");
            check(info.nonLocalizedLabel.toString().equals("Aplicación ñ 📺"),"UTF-16 manifest text");
        } else check((info.flags&ApplicationInfo.FLAG_HAS_CODE)!=0,"Default hasCode=true");
        info.targetSdkVersion=999;
        check(context.getApplicationInfo().targetSdkVersion==Integer.parseInt(args[5]),"Metadata snapshot protected");
        AppEnvironment.current().resources.close();
        System.out.println("AOSP_APPLICATION_INFO_OK package="+args[4]+" target="+args[5]+" uid="+info.uid);
    }
}
