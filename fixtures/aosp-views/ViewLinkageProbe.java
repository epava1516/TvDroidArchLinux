package org.archtv.aospprobe;

/** Diagnostic only: a failure is recorded, never replaced by a successful stub. */
public final class ViewLinkageProbe {
    private static void verifyStateSet() {
        int[] bits = {4,1,8,2,16,32,64,128,256,512};
        int[] ids = {16842908,16842909,16842910,16842913,16842919,16843518,16843547,16843623,16843624,16843625};
        for (int mask=0; mask<1024; mask++) {
            int[] actual = android.util.StateSet.get(mask);
            if (actual.length != Integer.bitCount(mask)) throw new AssertionError("State count");
            int cursor=0;
            for (int i=0; i<ids.length; i++) {
                boolean present = (mask & bits[i]) != 0;
                if (present && actual[cursor++] != ids[i]) throw new AssertionError("State ID/order");
                if (android.util.StateSet.stateSetMatches(new int[]{ids[i]},actual) != present)
                    throw new AssertionError("Required state match");
                if (android.util.StateSet.stateSetMatches(new int[]{-ids[i]},actual) == present)
                    throw new AssertionError("Prohibited state match");
            }
        }
        try { android.util.StateSet.get(1024); throw new AssertionError("Invalid mask accepted"); }
        catch (IllegalArgumentException expected) { }
        System.out.println("VIEW_STATESET_OK masks=1024");
    }
    private static void verifyMeasurement() {
        int exact = android.view.View.MeasureSpec.makeMeasureSpec(80,android.view.View.MeasureSpec.EXACTLY);
        int limit = android.view.View.MeasureSpec.makeMeasureSpec(80,android.view.View.MeasureSpec.AT_MOST);
        int free = android.view.View.MeasureSpec.makeMeasureSpec(0,android.view.View.MeasureSpec.UNSPECIFIED);
        if (android.view.View.MeasureSpec.getMode(exact) != android.view.View.MeasureSpec.EXACTLY
                || android.view.View.MeasureSpec.getSize(exact) != 80
                || android.view.View.resolveSize(40,exact) != 80
                || android.view.View.resolveSize(40,limit) != 40
                || android.view.View.resolveSize(100,limit) != 80
                || android.view.View.resolveSize(40,free) != 40
                || android.view.View.resolveSizeAndState(100,limit,0) != (80|android.view.View.MEASURED_STATE_TOO_SMALL)
                || android.view.View.getDefaultSize(40,limit) != 80)
            throw new AssertionError("Original measurement helpers");
        System.out.println("VIEW_MEASUREMENT_HELPERS_OK");
    }
    public static void main(String[] args) throws Exception {
        System.load(args[0]);
        System.load(args[1]);
        verifyStateSet();
        for (String name : new String[]{"android.view.View", "android.view.ViewGroup", "android.view.ContextThemeWrapper"}) {
            System.out.println("VIEW_LINKAGE_BEGIN "+name);
            try {
                Class<?> type = Class.forName(name, true, ViewLinkageProbe.class.getClassLoader());
                System.out.println("VIEW_LINKAGE_INITIALIZED "+name);
                // Resolve public signatures too: successful initialization alone is insufficient.
                System.out.println("VIEW_LINKAGE_LOADED "+name+" constructors="+type.getConstructors().length);
                if (name.equals("android.view.View")) verifyMeasurement();
            } catch (LinkageError | ClassNotFoundException failure) {
                System.out.println("VIEW_LINKAGE_BLOCKED "+name+" "+failure);
                failure.printStackTrace(System.err);
            }
        }
        System.out.println("VIEW_LINKAGE_DIAGNOSTIC_DONE");
    }
}
