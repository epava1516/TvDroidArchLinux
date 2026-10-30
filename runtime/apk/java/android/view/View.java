package android.view;

import android.content.Context;
import org.archtv.apkruntime.AppEnvironment;

public class View {
    public interface OnClickListener { void onClick(View view); }
    protected final Context context;
    private OnClickListener listener;
    private final int[] padding = new int[4];
    private ViewGroup parent;
    public View(Context context) {
        if (context == null) throw new NullPointerException("context");
        this.context = context;
    }
    public void setOnClickListener(OnClickListener value) { listener = value; }
    public boolean performClick() {
        if (listener == null) return false;
        listener.onClick(this);
        return true;
    }
    public final boolean requestFocus() {
        AppEnvironment.current().focus = this;
        return true;
    }
    public void setPadding(int left, int top, int right, int bottom) {
        padding[0] = left; padding[1] = top; padding[2] = right; padding[3] = bottom;
    }
    public final int[] hostPadding() { return padding.clone(); }
    public final void hostAttach(ViewGroup value) {
        if (parent != null || value == this) throw new IllegalStateException("View already attached or cyclic");
        for (View cursor = value; cursor != null; cursor = cursor.parent) {
            if (cursor == this) throw new IllegalStateException("Cyclic View tree");
        }
        parent = value;
    }
}
