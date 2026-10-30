// Compile-only Java 8 bootstrap declaration missing from the SDK reference.
// D8 desugars these lambdas; this class is never packaged in the runtime DEX.
package java.lang.invoke;
public final class LambdaMetafactory {
    public static native CallSite metafactory(MethodHandles.Lookup caller, String name,
        MethodType invokedType, MethodType samMethodType, MethodHandle implementation,
        MethodType instantiatedMethodType) throws LambdaConversionException;
}
