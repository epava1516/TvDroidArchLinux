package org.archtv.apkruntime;

import android.content.pm.ApplicationInfo;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;

/** Linux metadata adapter; binary XML decoding remains in original androidfw. */
public final class ApkMetadata {
    private static native String[] nativeRead(String path);
    private static final class Value {
        final int type;
        final String text;
        Value(String type, String text) { this.type=Integer.parseInt(type); this.text=text; }
    }
    private final Map<String,Value> values = new HashMap<String,Value>();
    private ApkMetadata(Path apk) {
        String[] raw=nativeRead(apk.toAbsolutePath().normalize().toString());
        if(raw==null || raw.length%3!=0)throw new IllegalStateException("Invalid native manifest result");
        for(int i=0;i<raw.length;i+=3) {
            if(values.put(raw[i],new Value(raw[i+1],raw[i+2]))!=null)
                throw new IllegalArgumentException("Duplicate manifest metadata");
        }
    }
    private String text(String key,String fallback) {
        Value value=values.get(key);
        if(value==null)return fallback;
        if(value.type!=3)throw new UnsupportedOperationException("Manifest string must be literal: "+key);
        return value.text;
    }
    private int integer(String key,int fallback) {
        Value value=values.get(key);
        if(value==null)return fallback;
        if(value.type!=16 && value.type!=17)
            throw new UnsupportedOperationException("Manifest integer must be numeric: "+key);
        long number=Long.parseLong(value.text);
        if(number<0 || number>Integer.MAX_VALUE)throw new IllegalArgumentException("Manifest integer range: "+key);
        return (int)number;
    }
    private boolean bool(String key,boolean fallback) {
        Value value=values.get(key);
        if(value==null)return fallback;
        if(value.type!=18 && value.type!=16 && value.type!=17)
            throw new UnsupportedOperationException("Manifest boolean must be literal: "+key);
        return Long.parseLong(value.text)!=0;
    }
    private int resource(String key) {
        Value value=values.get(key);
        if(value==null || value.type==0)return 0;
        if(value.type!=1)throw new UnsupportedOperationException("Manifest resource ID required: "+key);
        return (int)Long.parseLong(value.text);
    }
    private static String className(String pkg,String name) {
        if(name==null || name.isEmpty())return null;
        return name.startsWith(".")?pkg+name:name.indexOf('.')<0?pkg+"."+name:name;
    }
    public static ApplicationInfo read(Path apk,Path data) {
        ApkMetadata metadata=new ApkMetadata(apk);
        ApplicationInfo info=new ApplicationInfo();
        if(!metadata.values.containsKey("application/@present"))
            throw new UnsupportedOperationException("An application manifest entry is required");
        info.packageName=metadata.text("manifest/package",null);
        if(info.packageName==null || !info.packageName.matches("[A-Za-z_][A-Za-z0-9_]*(\\.[A-Za-z_][A-Za-z0-9_]*)+"))
            throw new IllegalArgumentException("Invalid or missing manifest package");
        if(metadata.values.containsKey("manifest/split"))
            throw new UnsupportedOperationException("Split APK metadata is not supported");
        // PackageParser's original numeric uses-sdk defaults. With no tag,
        // preserve the original ApplicationInfo zero-valued fields.
        if(metadata.values.containsKey("uses-sdk/@present")) {
            info.minSdkVersion=metadata.integer("uses-sdk/android:minSdkVersion",1);
            info.targetSdkVersion=metadata.integer("uses-sdk/android:targetSdkVersion",info.minSdkVersion);
        }
        if(info.minSdkVersion>android.os.Build.VERSION.SDK_INT)
            throw new UnsupportedOperationException("APK requires a newer platform SDK");
        info.uid=metadata.integer("host/uid",-1);
        info.sourceDir=info.publicSourceDir=apk.toAbsolutePath().normalize().toString();
        info.dataDir=data.toAbsolutePath().normalize().toString();
        info.className=className(info.packageName,metadata.text("application/android:name",null));
        String process=metadata.text("application/android:process",info.packageName);
        info.processName=process.startsWith(":")?info.packageName+process:process;
        info.enabled=metadata.bool("application/android:enabled",true);
        info.flags=ApplicationInfo.FLAG_INSTALLED;
        String[] attributes={"hasCode","debuggable","allowBackup","allowClearUserData","hardwareAccelerated",
                             "supportsRtl","largeHeap","extractNativeLibs","multiArch"};
        int[] flags={ApplicationInfo.FLAG_HAS_CODE,ApplicationInfo.FLAG_DEBUGGABLE,ApplicationInfo.FLAG_ALLOW_BACKUP,
            ApplicationInfo.FLAG_ALLOW_CLEAR_USER_DATA,ApplicationInfo.FLAG_HARDWARE_ACCELERATED,
            ApplicationInfo.FLAG_SUPPORTS_RTL,ApplicationInfo.FLAG_LARGE_HEAP,ApplicationInfo.FLAG_EXTRACT_NATIVE_LIBS,
            ApplicationInfo.FLAG_MULTIARCH};
        boolean[] defaults={true,false,true,true,info.targetSdkVersion>=14,false,false,true,false};
        for(int i=0;i<attributes.length;i++)
            if(metadata.bool("application/android:"+attributes[i],defaults[i]))info.flags|=flags[i];
        String[] screens={"smallScreens","normalScreens","largeScreens","xlargeScreens","resizeable","anyDensity"};
        int[] screenFlags={ApplicationInfo.FLAG_SUPPORTS_SMALL_SCREENS,ApplicationInfo.FLAG_SUPPORTS_NORMAL_SCREENS,
            ApplicationInfo.FLAG_SUPPORTS_LARGE_SCREENS,ApplicationInfo.FLAG_SUPPORTS_XLARGE_SCREENS,
            ApplicationInfo.FLAG_RESIZEABLE_FOR_SCREENS,ApplicationInfo.FLAG_SUPPORTS_SCREEN_DENSITIES};
        boolean[] screenDefaults={info.targetSdkVersion>=4,true,info.targetSdkVersion>=4,info.targetSdkVersion>=9,
                                  info.targetSdkVersion>=4,info.targetSdkVersion>=4};
        for(int i=0;i<screens.length;i++)
            if(metadata.bool("supports-screens/android:"+screens[i],screenDefaults[i]))info.flags|=screenFlags[i];
        Value label=metadata.values.get("application/android:label");
        if(label!=null && label.type==3)info.nonLocalizedLabel=label.text;
        else info.labelRes=metadata.resource("application/android:label");
        info.icon=metadata.resource("application/android:icon");
        info.theme=metadata.resource("application/android:theme");
        return info;
    }
}
