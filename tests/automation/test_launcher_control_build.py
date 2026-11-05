"""Host regressions for own launcher encoding bounds; no Android/API/MAC proof."""
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
JAVA = r'''
package org.archtv.aosplinux;
import java.io.*;
import java.lang.reflect.*;
import java.nio.charset.*;
public class LauncherControlEncodingTest {
    private static void rejected(Method method,Object... args) throws Exception {
        try {method.invoke(null,args);throw new AssertionError("Invalid encoding accepted");}
        catch(InvocationTargetException expected) {
            if(!(expected.getCause() instanceof IOException))throw expected;
        }
    }
    public static void main(String[] args) throws Exception {
        Method utf8=LauncherControlBridge.class.getDeclaredMethod("utf8",byte[].class);utf8.setAccessible(true);
        String label="Aplicación 日本語";
        if(!label.equals(utf8.invoke(null,(Object)label.getBytes(StandardCharsets.UTF_8))))throw new AssertionError();
        for(byte[] bad:new byte[][]{{(byte)0xc0,(byte)0xaf},{(byte)0xed,(byte)0xa0,(byte)0x80},{(byte)0xe2,(byte)0x82},{(byte)0xff}})
            rejected(utf8,(Object)bad);
        Method string=LauncherControlBridge.class.getDeclaredMethod("string",DataOutputStream.class,String.class,int.class);string.setAccessible(true);
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();DataOutputStream out=new DataOutputStream(bytes);
        string.invoke(null,out,"é",2);
        DataInputStream in=new DataInputStream(new ByteArrayInputStream(bytes.toByteArray()));
        if(in.readInt()!=2 || in.readUnsignedByte()!=0xc3 || in.readUnsignedByte()!=0xa9 || in.read()!=-1)throw new AssertionError();
        rejected(string,out,"é",1);
        try {WaylandInputBridge.createServer("arbitrary-endpoint");throw new AssertionError();}
        catch(IllegalArgumentException expected){}
        System.out.println("8 host encoding/endpoint-bound regressions passed; no Android execution or peer/MAC acceptance");
    }
}
'''

class LauncherControlEncoding(unittest.TestCase):
    def test_real_adapter_encoding_and_endpoint_bounds(self):
        source = ROOT / 'runtime/aosp/linux-services/org/archtv/aosplinux'
        with tempfile.TemporaryDirectory(prefix='archtv-launcher-encoding-') as directory:
            work = pathlib.Path(directory)
            harness = work / 'LauncherControlEncodingTest.java'
            harness.write_text(JAVA)
            subprocess.run(['javac', '--release', '8', '-d', str(work),
                            *[str(source / name) for name in ['LauncherControlBridge.java',
                              'WaylandInputBridge.java', 'TaskFocusObserver.java']],
                            str(harness)], check=True, capture_output=True, timeout=60)
            result = subprocess.run(['java', '-cp', str(work),
                         'org.archtv.aosplinux.LauncherControlEncodingTest'],
                         check=True, capture_output=True, text=True, timeout=30)
            self.assertIn('8 host encoding/endpoint-bound regressions passed', result.stdout)

if __name__ == '__main__':
    unittest.main()
