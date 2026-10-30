package org.archtv.aospprobe;

/** Diagnostic only: a failure is recorded, never replaced by a successful stub. */
public final class ViewLinkageProbe {
    public static void main(String[] args) throws Exception {
        System.load(args[0]);
        System.load(args[1]);
        for (String name : new String[]{"android.view.View", "android.view.ViewGroup", "android.view.ContextThemeWrapper"}) {
            System.out.println("VIEW_LINKAGE_BEGIN "+name);
            try {
                Class<?> type = Class.forName(name, true, ViewLinkageProbe.class.getClassLoader());
                // Resolve public signatures too: successful initialization alone is insufficient.
                System.out.println("VIEW_LINKAGE_LOADED "+name+" constructors="+type.getConstructors().length);
            } catch (LinkageError | ClassNotFoundException failure) {
                System.out.println("VIEW_LINKAGE_BLOCKED "+name+" "+failure);
                failure.printStackTrace(System.err);
            }
        }
        System.out.println("VIEW_LINKAGE_DIAGNOSTIC_DONE");
    }
}
