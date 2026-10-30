package org.archtv.metrics;

import android.app.Activity;
import android.app.Application;
import android.content.ComponentCallbacks2;
import android.content.res.Configuration;
import android.os.Bundle;
import android.os.Looper;
import android.util.DisplayMetrics;
import android.widget.TextView;

/** Owned APK using only public SDK APIs; no host classes or test protocol calls. */
public final class MainActivity extends Activity {
    private Application application;
    private TextView label;
    private int changes;
    private final ComponentCallbacks2 listener = new ComponentCallbacks2() {
        @Override public void onConfigurationChanged(Configuration configuration) {
            DisplayMetrics metrics = getResources().getDisplayMetrics();
            if (configuration.screenWidthDp != (int)(metrics.widthPixels / metrics.density)
                    || configuration.screenHeightDp != (int)(metrics.heightPixels / metrics.density))
                throw new AssertionError("Callback arrived before Resources update");
            int orientation = metrics.widthPixels >= metrics.heightPixels
                ? Configuration.ORIENTATION_LANDSCAPE : Configuration.ORIENTATION_PORTRAIT;
            if (configuration.orientation != orientation) throw new AssertionError("Wrong orientation");
            changes++;
            refresh();
        }
        @Override public void onLowMemory() { }
        @Override public void onTrimMemory(int level) { }
    };
    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        application = (Application)getApplicationContext();
        if (!"Arch TV · Context metrics".equals(getString(R.string.app_name)))
            throw new AssertionError("Wrong APK resources");
        if (application.getResources() != getResources())
            throw new AssertionError("Application and Activity resources differ");
        label = new TextView(this);
        label.setPadding(24,24,24,24);
        label.setTextSize(28);
        setContentView(label);
        application.registerComponentCallbacks(listener);
        refresh();
    }
    private void refresh() {
        if (Looper.myLooper() != getMainLooper())
            throw new AssertionError("Application callback off the main Looper");
        DisplayMetrics metrics = getResources().getDisplayMetrics();
        String message = "Metrics: "+metrics.widthPixels+"x"+metrics.heightPixels+" callbacks="+changes;
        label.setText(message);
        System.err.println("APK_METRICS "+message+" thread="+Thread.currentThread().getName());
    }
    @Override protected void onDestroy() {
        if (application != null) application.unregisterComponentCallbacks(listener);
        super.onDestroy();
    }
}
