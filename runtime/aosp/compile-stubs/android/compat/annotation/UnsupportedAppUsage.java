// Compile-only metadata absent from the framework reference jar. Never package this class.
package android.compat.annotation;
public @interface UnsupportedAppUsage {
    int maxTargetSdk() default Integer.MAX_VALUE;
    long trackingBug() default 0;
}
