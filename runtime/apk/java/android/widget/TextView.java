package android.widget;

import android.content.Context;
import android.view.View;

public class TextView extends View {
    private String text = "";
    private float textSize = 14;
    public TextView(Context context) { super(context); }
    public final void setText(CharSequence value) { text = value == null ? "" : value.toString(); }
    public final void setText(int resourceId) { setText(context.getString(resourceId)); }
    public void setTextSize(float value) {
        if (Float.isNaN(value) || Float.isInfinite(value) || value < 0 || value > 1024)
            throw new IllegalArgumentException("Unsupported text size");
        textSize = value;
    }
    public final String hostText() { return text; }
    public final float hostTextSize() { return textSize; }
}
