import java.io.File;
import java.util.*;
import com.android.tools.smali.dexlib2.*;
import com.android.tools.smali.dexlib2.iface.*;
import com.android.tools.smali.dexlib2.iface.instruction.*;
import com.android.tools.smali.dexlib2.iface.reference.StringReference;
import com.android.tools.smali.dexlib2.immutable.*;
import com.android.tools.smali.dexlib2.immutable.reference.ImmutableStringReference;
import com.android.tools.smali.dexlib2.immutable.instruction.*;
import com.android.tools.smali.dexlib2.rewriter.*;
/** Rewrite only the original fork's target instruction; preserve shared strings elsewhere. */
public final class ZygoteSelectedEntryPlan {
    static final String OLD="com.android.server.SystemServer", NEW="archtv.runtime.SelectedRuntime";
    static boolean target(Method m) { return m.getDefiningClass().equals("Lcom/android/internal/os/ZygoteInit;") && m.getName().equals("forkSystemServer"); }
    static boolean targetString(Instruction i,String value) {return i instanceof ReferenceInstruction ref && ref.getReference() instanceof StringReference str && str.getString().equals(value);}
    static int count(DexFile d,String value) {int n=0;for(var c:d.getClasses())for(var m:c.getMethods())if(m.getImplementation()!=null)for(var i:m.getImplementation().getInstructions())if(targetString(i,value))n++;return n;}
    static void interfaces(Class<?> type,Set<Class<?>> out) {
        if(type==null)return;for(var i:type.getInterfaces()){out.add(i);interfaces(i,out);}interfaces(type.getSuperclass(),out);
    }
    static String value(Object object) {
        if(object instanceof SwitchElement element)return element.getKey()+":"+element.getOffset();
        if(object instanceof Iterable<?> values){StringBuilder s=new StringBuilder("[");for(Object v:values)s.append(value(v)).append(",");return s.append("]").toString();}
        return String.valueOf(object);
    }
    static String signature(Instruction insn) throws Exception {
        TreeMap<String,String> result=new TreeMap<>();Set<Class<?>> interfaces=new HashSet<>();interfaces(insn.getClass(),interfaces);
        for(var type:interfaces)for(var m:type.getMethods())if(m.getName().startsWith("get") && m.getParameterCount()==0)result.put(m.getName(),value(m.invoke(insn)));
        return result.toString();
    }
    public static void main(String[] args) throws Exception {
        var container=DexFileFactory.loadDexContainer(new File(args[0]),Opcodes.forDexVersion(39));int changed=0;
        for(String entry:container.getDexEntryNames()) {
            var original=container.getEntry(entry).getDexFile();boolean found=false;
            for(var c:original.getClasses())for(var m:c.getMethods())if(target(m) && m.getImplementation()!=null)for(var i:m.getImplementation().getInstructions())if(targetString(i,OLD))found=true;
            if(!found)continue;
            final int[] changes={0};
            var rewriter=new DexRewriter(new RewriterModule(){
                @Override public Rewriter<Method> getMethodRewriter(Rewriters rw) {
                    return method->{
                        if(!target(method))return method;
                        var impl=method.getImplementation();List<Instruction> instructions=new ArrayList<>();
                        for(var i:impl.getInstructions()) {
                            if(targetString(i,OLD)) {
                                var ref=new ImmutableStringReference(NEW);
                                if(i.getOpcode()==Opcode.CONST_STRING) i=new ImmutableInstruction21c(Opcode.CONST_STRING,((OneRegisterInstruction)i).getRegisterA(),ref);
                                else if(i.getOpcode()==Opcode.CONST_STRING_JUMBO)i=new ImmutableInstruction31c(Opcode.CONST_STRING_JUMBO,((OneRegisterInstruction)i).getRegisterA(),ref);
                                else throw new IllegalStateException("Unexpected original opcode");
                                changes[0]++;
                            }
                            instructions.add(i);
                        }
                        return new ImmutableMethod(method.getDefiningClass(),method.getName(),method.getParameters(),method.getReturnType(),method.getAccessFlags(),method.getAnnotations(),method.getHiddenApiRestrictions(),new ImmutableMethodImplementation(impl.getRegisterCount(),instructions,impl.getTryBlocks(),impl.getDebugItems()));
                    };
                }
            });
            File output=new File(args[1]);DexFileFactory.writeDexFile(output.toString(),rewriter.getDexFileRewriter().rewrite(original));
            var adapted=DexFileFactory.loadDexFile(output,Opcodes.forDexVersion(39));
            if(changes[0]!=1 || count(adapted,OLD)!=count(original,OLD)-1 || count(adapted,NEW)!=1)throw new IllegalStateException("Reference census changed unexpectedly");
            Map<String,Method> after=new HashMap<>();for(var c:adapted.getClasses())for(var m:c.getMethods())after.put(m.toString(),m);
            int differences=0, methods=0;
            for(var c:original.getClasses())for(var m:c.getMethods()) {
                var n=after.remove(m.toString());if(n==null)throw new IllegalStateException("Method removed");methods++;
                var a=m.getImplementation();var b=n.getImplementation();if((a==null)!=(b==null))throw new IllegalStateException("Implementation changed");if(a==null)continue;
                if(a.getRegisterCount()!=b.getRegisterCount())throw new IllegalStateException("Registers changed");
                var ia=a.getInstructions().iterator();var ib=b.getInstructions().iterator();
                while(ia.hasNext() && ib.hasNext()) {
                    var x=ia.next();var y=ib.next();
                    if(!signature(x).equals(signature(y))) {
                        if(!target(m)||!targetString(x,OLD)||!targetString(y,NEW)||x.getOpcode()!=y.getOpcode()||x.getCodeUnits()!=y.getCodeUnits()||((OneRegisterInstruction)x).getRegisterA()!=((OneRegisterInstruction)y).getRegisterA())throw new IllegalStateException("Unexpected instruction difference: "+m+" BEFORE="+signature(x)+" AFTER="+signature(y));
                        differences++;
                    }
                }
                if(ia.hasNext()||ib.hasNext())throw new IllegalStateException("Instruction count changed");
            }
            if(!after.isEmpty()||differences!=1)throw new IllegalStateException("Unexpected executable changes");
            changed++;System.out.println(entry+" "+methods+" "+differences+" "+count(original,OLD));
        }
        if(changed!=1)throw new IllegalStateException("Expected one original target DEX");
    }
}
