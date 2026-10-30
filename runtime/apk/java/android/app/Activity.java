package android.app;

import android.content.Context;
import android.os.Bundle;
import android.view.View;

/** Measured lifecycle subset, not the full Android Activity implementation. */
public class Activity extends Context {
    private View content;
    private boolean created;
    protected void onCreate(Bundle state) { }
    protected void onStart() { }
    protected void onResume() { }
    protected void onPause() { }
    protected void onStop() { }
    protected void onDestroy() { }
    public void setContentView(View view) {
        if (view == null) throw new NullPointerException("content");
        content = view;
    }
    public final View hostContentView() { return content; }
    public final void hostCreate() {
        if (created) throw new IllegalStateException("Activity already created");
        created = true;
        onCreate(null);
        onStart();
        onResume();
    }
    public final void hostDestroy() {
        if (!created) throw new IllegalStateException("Activity not created");
        onPause();
        onStop();
        onDestroy();
        content = null;
        created = false;
    }
}
