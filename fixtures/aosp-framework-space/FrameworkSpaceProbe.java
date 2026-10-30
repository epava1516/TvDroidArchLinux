package org.archtv.aospprobe;
/** Link original framework/app types without class initialization or application execution. */
public final class FrameworkSpaceProbe {
    public static void main(String[] args) throws Exception {
        ClassLoader loader=FrameworkSpaceProbe.class.getClassLoader();
        Class<?> activity=Class.forName("android.app.Activity",false,loader);
        for(String name:new String[]{"android.app.Application","android.view.View","android.view.LayoutInflater",args[0]}) {
            Class<?> type=Class.forName(name,false,loader);
            if(name.equals(args[0]) && !activity.isAssignableFrom(type))throw new AssertionError("Not an original Activity subtype");
            System.out.println("FRAMEWORK_CLASS_LINK_OK "+type.getName());
        }
        System.out.println("FRAMEWORK_SPACE_ONLY_OK no_app_execution");
    }
}
