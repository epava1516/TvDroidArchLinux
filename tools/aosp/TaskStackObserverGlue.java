import java.io.File;
import java.util.*;
import com.android.tools.smali.dexlib2.*;
import com.android.tools.smali.dexlib2.iface.*;
import com.android.tools.smali.dexlib2.immutable.*;
import com.android.tools.smali.dexlib2.immutable.reference.*;
import com.android.tools.smali.dexlib2.immutable.instruction.*;

/** One Linux adapter subclass; the complete Binder listener remains original. */
public final class TaskStackObserverGlue {
    public static void main(String[] args) throws Exception {
        String parent="Landroid/app/TaskStackListener;";
        ClassDef original=null;
        // The pinned original framework and our basic glue use DEX039. This
        // encoding version is independent of Android36's runtime API level.
        var container=DexFileFactory.loadDexContainer(new File(args[0]),Opcodes.forDexVersion(39));
        for(String entry:container.getDexEntryNames())
            for(var type:container.getEntry(entry).getDexFile().getClasses())
                if(type.getType().equals(parent)) {
                    if(original!=null)throw new IllegalStateException("Duplicate original listener");
                    original=type;
                }
        if(original==null || !"Landroid/app/ITaskStackListener$Stub;".equals(original.getSuperclass()))
            throw new IllegalStateException("Original Binder listener parent missing");
        boolean constructor=false,callback=false;
        for(var method:original.getMethods()) {
            if((method.getAccessFlags()&AccessFlags.ABSTRACT.getValue())!=0)
                throw new IllegalStateException("Original listener requires another callback implementation");
            boolean publicMethod=(method.getAccessFlags()&AccessFlags.PUBLIC.getValue())!=0;
            if(publicMethod && method.getParameterTypes().isEmpty() && method.getReturnType().equals("V")) {
                constructor|=method.getName().equals("<init>") && method.getImplementation()!=null;
                callback|=method.getName().equals("onTaskStackChanged") && method.getImplementation()!=null
                    && (method.getAccessFlags()&AccessFlags.FINAL.getValue())==0;
            }
        }
        if(!constructor || !callback)throw new IllegalStateException("Original executable listener ABI mismatch");
        String own="Lorg/archtv/aosplinux/OriginalTaskStackObserver;";
        var field=new ImmutableField(own,"callback","Ljava/lang/Runnable;",
            AccessFlags.PRIVATE.getValue()|AccessFlags.FINAL.getValue(),null,Set.of(),Set.of());
        var reference=new ImmutableFieldReference(own,"callback","Ljava/lang/Runnable;");
        var ctor=new ImmutableMethod(own,"<init>",List.of(new ImmutableMethodParameter("Ljava/lang/Runnable;",Set.of(),"callback")),"V",
            AccessFlags.PUBLIC.getValue()|AccessFlags.CONSTRUCTOR.getValue(),Set.of(),Set.of(),
            new ImmutableMethodImplementation(2,List.of(
                new ImmutableInstruction35c(Opcode.INVOKE_DIRECT,1,0,0,0,0,0,new ImmutableMethodReference(parent,"<init>",List.of(),"V")),
                new ImmutableInstruction22c(Opcode.IPUT_OBJECT,1,0,reference),
                new ImmutableInstruction10x(Opcode.RETURN_VOID)),List.of(),List.of()));
        Set<String> callbacks=Set.of("onTaskStackChanged","onTaskFocusChanged","onTaskMovedToFront","onTaskRemoved","onTaskCreated","onTaskDisplayChanged");
        Set<String> found=new HashSet<>();List<Method> methods=new ArrayList<>();methods.add(ctor);
        for(var method:original.getMethods())if(callbacks.contains(method.getName())) {
            if(!method.getReturnType().equals("V") || (method.getAccessFlags()&AccessFlags.FINAL.getValue())!=0)
                throw new IllegalStateException("Original callback cannot be adapted");
            List<ImmutableMethodParameter> parameters=new ArrayList<>();
            for(var parameter:method.getParameterTypes()) {
                if(parameter.equals("J") || parameter.equals("D"))throw new IllegalStateException("Unexpected wide callback parameter");
                parameters.add(new ImmutableMethodParameter(parameter.toString(),Set.of(),null));
            }
            methods.add(new ImmutableMethod(own,method.getName(),parameters,"V",AccessFlags.PUBLIC.getValue(),Set.of(),Set.of(),
                new ImmutableMethodImplementation(2+parameters.size(),List.of(
                    new ImmutableInstruction22c(Opcode.IGET_OBJECT,0,1,reference),
                    new ImmutableInstruction35c(Opcode.INVOKE_INTERFACE,1,0,0,0,0,0,new ImmutableMethodReference("Ljava/lang/Runnable;","run",List.of(),"V")),
                    new ImmutableInstruction10x(Opcode.RETURN_VOID)),List.of(),List.of())));
            found.add(method.getName());
        }
        if(!found.equals(callbacks))throw new IllegalStateException("Required original task callbacks missing");
        var ownClass=new ImmutableClassDef(own,AccessFlags.PUBLIC.getValue()|AccessFlags.FINAL.getValue(),parent,List.of(),"TaskStackObserverGlue.java",Set.of(),List.of(field),methods);
        DexFileFactory.writeDexFile(args[1],new ImmutableDexFile(Opcodes.forDexVersion(39),List.of(ownClass)));
        System.out.println("Original executable TaskStackListener ABI verified; generated one own subclass, no android.* replacement");
    }
}
