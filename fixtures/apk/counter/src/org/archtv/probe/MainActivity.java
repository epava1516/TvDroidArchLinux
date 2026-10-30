package org.archtv.probe;

import android.app.Activity;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

/** APK fixture: exercises framework calls, click input and persistent app state. */
public final class MainActivity extends Activity implements View.OnClickListener {
    private SharedPreferences preferences;
    private TextView label;
    private int count;

    @Override
    public void onCreate(Bundle savedState) {
        super.onCreate(savedState);
        preferences = getSharedPreferences("counter", MODE_PRIVATE);
        count = preferences.getInt("count", 0);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(24, 24, 24, 24);
        label = new TextView(this);
        label.setTextSize(28);
        refresh();
        Button increment = new Button(this);
        increment.setText(R.string.increment);
        increment.setOnClickListener(this);
        layout.addView(label);
        layout.addView(increment);
        setContentView(layout);
        increment.requestFocus();
    }

    private void refresh() {
        label.setText(getString(R.string.counter) + " " + count);
    }

    @Override
    public void onClick(View view) {
        count++;
        preferences.edit().putInt("count", count).commit();
        refresh();
    }
}
