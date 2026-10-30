package android.view;

import android.content.Context;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class ViewGroup extends View {
    private final List<View> children = new ArrayList<View>();
    public ViewGroup(Context context) { super(context); }
    public void addView(View child) {
        if (child == null) throw new NullPointerException("child");
        child.hostAttach(this);
        children.add(child);
    }
    public final List<View> hostChildren() { return Collections.unmodifiableList(children); }
}
