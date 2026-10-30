import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Paths;
import java.util.Arrays;

/** Build-time check only; reference bytecode is never copied into the runtime. */
public final class ResourceBindingCheck {
    public static void main(String[] args) throws Exception {
        try (URLClassLoader generated = new URLClassLoader(new URL[]{Paths.get(args[0]).toUri().toURL()}, null);
             URLClassLoader reference = new URLClassLoader(new URL[]{Paths.get(args[1]).toUri().toURL()}, null)) {
            int[] actual = (int[])generated.loadClass("com.android.internal.R$styleable")
                .getField("ViewDrawableStates").get(null);
            int[] expected = (int[])reference.loadClass("com.android.internal.R$styleable")
                .getField("ViewDrawableStates").get(null);
            if (!Arrays.equals(actual, expected)) throw new AssertionError("State resource IDs/order differ");
            System.out.println("VIEW_RESOURCE_BINDING_OK "+Arrays.toString(actual));
        }
    }
}
