package org.archtv.runtimeprobe;

/** Host ART execution probe. It deliberately supplies no android.* classes. */
public final class RuntimeProbe {
    private interface Operation { int apply(int value); }
    private static final class Increment implements Operation {
        public int apply(int value) { return value + 1; }
    }
    private static int factorial(int value) {
        return value < 2 ? 1 : value * factorial(value - 1);
    }
    public static void main(String[] args) throws Exception {
        Operation operation = new Increment();
        int total = 0;
        for (int value : new int[] {1, 2, 3}) total += operation.apply(value);
        long wide = Long.parseLong("1099511627776");
        double square = Double.parseDouble("81.0");
        if (Class.forName("java.lang.String") != String.class || total != 9 || factorial(6) != 720
                || operation.apply(Integer.MAX_VALUE) != Integer.MIN_VALUE
                || wide + 3 != 1099511627779L
                || Math.abs(Math.sqrt(square) - 9.0) > 0.00001) {
            throw new AssertionError("DEX semantic probe failed");
        }
        try {
            Integer.parseInt("invalid");
            throw new AssertionError("Expected NumberFormatException");
        } catch (NumberFormatException expected) {
            System.out.println("DEX_SEMANTICS_OK total=" + total);
        }
        if (args.length == 1) {
            // An unresolved Android superclass must fail explicitly. No fake success.
            Class<?> activity = Class.forName(args[0]);
            Object instance = activity.getDeclaredConstructor().newInstance();
            System.out.println("APK_CLASS_INSTANTIATED " + instance.getClass().getName());
        }
    }
}
