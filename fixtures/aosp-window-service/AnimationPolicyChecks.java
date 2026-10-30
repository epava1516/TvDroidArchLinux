package org.archtv.apkruntime;

import android.animation.ValueAnimator;
import android.view.animation.AccelerateDecelerateInterpolator;
import android.view.animation.LinearInterpolator;

/** Original policy and interpolation algorithms; no frame clock or rendering claim. */
final class AnimationPolicyChecks {
    private static void check(boolean value,String message) {
        if (!value) throw new AssertionError(message);
    }
    static void verify(float expected) {
        check(ValueAnimator.getDurationScale()==expected,"WindowManagerGlobal must apply the live host policy");
        final int[] changes={0};final float[] last={-1};
        ValueAnimator.DurationScaleChangeListener listener=value->{changes[0]++;last[0]=value;};
        check(ValueAnimator.registerDurationScaleChangeListener(listener),"Register scale listener");
        check(!ValueAnimator.registerDurationScaleChangeListener(listener),"Duplicate scale listener");
        try {
            ValueAnimator.setDurationScale(0.25f);check(last[0]==0.25f && ValueAnimator.areAnimatorsEnabled(),"Quarter scale callback");
            ValueAnimator.setDurationScale(0);check(last[0]==0 && !ValueAnimator.areAnimatorsEnabled(),"Disabled scale callback");
            ValueAnimator.setDurationScale(expected);check(last[0]==expected && changes[0]==3,"Restored host scale");
        } finally { check(ValueAnimator.unregisterDurationScaleChangeListener(listener),"Unregister scale listener");ValueAnimator.setDurationScale(expected); }
        check(changes[0]==3,"Unregistered listener called");
        LinearInterpolator linear=new LinearInterpolator();
        AccelerateDecelerateInterpolator smooth=new AccelerateDecelerateInterpolator();
        check(linear.getInterpolation(0.25f)==0.25f,"Original linear interpolation");
        for (float value:new float[]{0,0.5f,1})
            check(Math.abs(smooth.getInterpolation(value)-value)<0.000001f,"Original cosine interpolation");
        System.out.println("AOSP_ANIMATION_POLICY_OK scale="+expected+" callbacks=3 interpolators=2");
    }
}
