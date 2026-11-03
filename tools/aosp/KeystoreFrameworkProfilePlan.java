import java.io.File;
import java.util.*;
import com.android.tools.smali.dexlib2.*;
import com.android.tools.smali.dexlib2.iface.*;
import com.android.tools.smali.dexlib2.iface.debug.LineNumber;
import com.android.tools.smali.dexlib2.dexbacked.instruction.DexBackedInstruction;
public class KeystoreFrameworkProfilePlan {
 public static void main(String[] a) throws Exception {
  var c=DexFileFactory.loadDexContainer(new File(a[0]),Opcodes.forApi(36));
  String[][] targets={{"AndroidKeyStoreKeyGeneratorSpi","engineGenerateKey","380","1210","1200"},{"AndroidKeyStoreKeyPairGeneratorSpi","generateKeyPair","675","0140","1200"},{"AndroidKeyStoreSpi","setPrivateKeyEntry","354","1215","1205"},{"AndroidKeyStoreSpi","setSecretKeyEntry","899","020f1300","130f0000"}};
  for(var t:targets) {
   int matches=0;
   for(String n:c.getDexEntryNames())for(var cls:c.getEntry(n).getDexFile().getClasses()) {
    if(!cls.getType().equals("Landroid/security/keystore2/"+t[0]+";"))continue;
    for(var m:cls.getMethods()) {
     if(!m.getName().equals(t[1]) || m.getImplementation()==null)continue;
     var impl=m.getImplementation();TreeMap<Integer,Integer> lines=new TreeMap<>();
     for(var d:impl.getDebugItems())if(d instanceof LineNumber ln)lines.put(ln.getCodeAddress(),ln.getLineNumber());
     int address=0;
     for(var insn:impl.getInstructions()) {
      var line=lines.floorEntry(address);
      var raw=(DexBackedInstruction)insn;
      if(line!=null && line.getValue()==Integer.parseInt(t[2])) {
       byte[] bytes=new byte[insn.getCodeUnits()*2];
       for(int i=0;i<bytes.length;i++)bytes[i]=(byte)raw.dexFile.getDataBuffer().readUbyte(raw.instructionStart+i);
       String hex=HexFormat.of().formatHex(bytes);
       if(hex.equals(t[3])) {
        matches++;
        System.out.println("{\"dex\":\""+n+"\",\"class\":\""+cls.getType()+"\",\"method\":\""+m.getName()+"\",\"source_line\":"+t[2]+",\"offset\":"+raw.instructionStart+",\"before\":\""+hex+"\",\"after\":\""+t[4]+"\"}");
       }
      }
      address+=insn.getCodeUnits();
     }
    }
   }
   if(matches!=1)throw new IllegalStateException(Arrays.toString(t)+" matches="+matches);
  }
 }
}
