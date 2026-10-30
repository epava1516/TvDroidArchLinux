package org.archtv.apkruntime;

import android.content.Context;
import android.content.res.Configuration;
import android.content.res.Resources;
import android.util.DisplayMetrics;
import android.util.TypedValue;

/** Independent expectations for original AOSP defaults, read through original Resources. */
final class SystemResourcesChecks {
    private static void check(boolean value,String message) {
        if (!value) throw new AssertionError(message);
    }
    private static int id(Resources resources,String type,String name) {
        int id = resources.getIdentifier(name,type,"android");
        check((id>>>24)==1,"System package ID: "+name);
        TypedValue value = new TypedValue();
        resources.getValue(id,value,true);
        check(value.assetCookie==1,"System asset cookie: "+name);
        return id;
    }
    static void verify(Context context, String systemPath) throws Exception {
        android.content.res.ApkAssets unexpected = null;
        try {
            unexpected = android.content.res.ApkAssets.loadFromPath(systemPath,2);
            throw new AssertionError("Unsupported asset flags accepted");
        } catch (UnsupportedOperationException expected) { }
        finally { if (unexpected != null) unexpected.close(); }
        Resources resources = context.getResources();
        Configuration original = new Configuration(resources.getConfiguration());
        DisplayMetrics initial = new DisplayMetrics();initial.setTo(resources.getDisplayMetrics());
        try {
            for (int density : new int[]{160,320}) {
                DisplayMetrics metrics = new DisplayMetrics();metrics.setTo(initial);
                metrics.densityDpi=density;metrics.density=metrics.scaledDensity=density/160f;
                metrics.xdpi=metrics.ydpi=density;
                metrics.noncompatDensityDpi=density;metrics.noncompatDensity=metrics.noncompatScaledDensity=density/160f;
                metrics.noncompatXdpi=metrics.noncompatYdpi=density;
                Configuration config = new Configuration(original);config.densityDpi=density;
                resources.updateConfiguration(config,metrics);
                String[] dimensions={"config_scrollbarSize","config_horizontalScrollFactor","config_verticalScrollFactor",
                    "config_minScrollbarTouchTarget","config_viewConfigurationTouchSlop","config_viewConfigurationHoverSlop",
                    "config_viewMinFlingVelocity","config_viewMaxFlingVelocity"};
                int[] dp={4,64,64,48,8,4,50,8000};
                for (int i=0;i<dimensions.length;i++) {
                    int id=id(resources,"dimen",dimensions[i]);
                    check(resources.getDimensionPixelSize(id)==dp[i]*(density/160),"Dimension: "+dimensions[i]);
                }
                check(id(resources,"dimen","config_scrollbarSize")==0x010500d6,"Compiler/private ID match");
                int span=id(resources,"dimen","config_minScalingSpan");
                check(resources.getDimensionPixelSize(span)==(density==160?170:340),"27mm at host xdpi");
                TypedValue multiplier = new TypedValue();
                resources.getValue(id(resources,"dimen","config_ambiguousGestureMultiplier"),multiplier,true);
                check(multiplier.type==TypedValue.TYPE_FLOAT && multiplier.getFloat()==2.0f,"Original float");
                for (String name : new String[]{"config_preferKeepClearForFocus","config_showMenuShortcutsWhenKeyboardPresent","config_ui_enableFadingMarquee"})
                    check(!resources.getBoolean(id(resources,"bool",name)),"Original bool: "+name);
                String[] integers={"config_globalActionsKeyTimeout","config_overrideHasPermanentMenuKey","config_screenshotChordKeyTimeout",
                    "config_smartSelectionInitializedTimeoutMillis","config_smartSelectionInitializingTimeoutMillis"};
                int[] values={500,0,0,200,500};
                for (int i=0;i<integers.length;i++)
                    check(resources.getInteger(id(resources,"integer",integers[i]))==values[i],"Original integer: "+integers[i]);
                int counter=resources.getIdentifier("counter","string","org.archtv.probe");
                TypedValue text = new TypedValue();resources.getValue(counter,text,true);
                check((counter>>>24)==0x7f && text.assetCookie==2 && "Contador:".equals(resources.getString(counter)),"Application resource/cookie");
                System.out.println("SYSTEM_RESOURCES_OK count=18 density="+density+" app-cookie=2");
            }
        } finally { resources.updateConfiguration(original,initial); }
    }
}
