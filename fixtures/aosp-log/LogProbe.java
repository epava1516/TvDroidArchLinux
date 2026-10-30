package org.archtv.aospprobe;

import android.util.Log;
import java.nio.charset.StandardCharsets;

public final class LogProbe {
    private static void check(boolean value,String message) {
        if (!value) throw new AssertionError(message);
    }
    public static void main(String[] args) throws Exception {
        System.load(args[0]);
        int minimum = Integer.parseInt(args[1]);
        int global = Integer.parseInt(args[2]);
        for (int level=2;level<=7;level++) {
            check(Log.isLoggable("Probe",level)==(level>=minimum),"Tag threshold "+level);
            check(Log.isLoggable(null,level)==(level>=global),"Global threshold "+level);
        }
        check(!Log.isLoggable("Probe",0),"Invalid priority");
        check(Log.isLoggable(new String(new char[100]).replace('\0','x'),7)==(global<=7),"Long tag");
        java.lang.reflect.Method payload = Log.class.getDeclaredMethod("logger_entry_max_payload_native");
        payload.setAccessible(true);
        check(((Integer)payload.invoke(null))==4068,"Actual native payload budget");
        String message = "Hola ñ 📺";
        int written = Log.i("Probe",message);
        check(written==(minimum<=4?message.getBytes(StandardCharsets.UTF_8).length:-1),"Write/filter result");
        for (int channel : new int[]{1,3,4}) {
            String marker = "CHANNEL_"+channel;
            check(Log.println_native(channel,6,"Probe",marker)==(minimum<=6?marker.length():-1),"Text channel "+channel);
        }
        check(Log.println_native(2,4,"Probe","BINARY_BUFFER_REJECTED")<0,"Unsupported binary buffer");
        check(Log.println(0,"Probe","INVALID_PRIORITY_REJECTED")<0,"Invalid priority write");
        try { Log.i("Probe",(String)null); throw new AssertionError("Null message accepted"); }
        catch (NullPointerException expected) { }
        if (minimum<=4) {
            check(Log.i(null,"NULL_TAG_OK")== (global<=4?11:-1),"Null tag write/filter");
            String large = new String(new char[3000]).replace("\0","ñ");
            check(Log.i("Probe",large)==4060,"UTF8 truncation must not split a code point");
            String hugeTag = new String(new char[5000]).replace('\0','x');
            check(Log.i(hugeTag,"OVERSIZED_TAG_REJECTED")<0,"Oversized tag budget");
        }
        System.out.println("AOSP_LINUX_LOG_OK minimum="+minimum+" global="+global);
    }
}
