package android.widget;

import android.content.Context;
import android.view.ViewGroup;

public class LinearLayout extends ViewGroup {
    public static final int HORIZONTAL = 0;
    public static final int VERTICAL = 1;
    private int orientation = HORIZONTAL;
    public LinearLayout(Context context) { super(context); }
    public void setOrientation(int value) {
        if (value != HORIZONTAL && value != VERTICAL) throw new IllegalArgumentException("orientation");
        orientation = value;
    }
    public final int hostOrientation() { return orientation; }
}
