package org.archtv.aospprobe;

import android.util.Log;
import android.os.DeadSystemException;
import java.net.UnknownHostException;

public final class ThrowableLogProbe {
    private static void check(boolean value,String message) {
        if(!value)throw new AssertionError(message);
    }
    public static void main(String[] args) throws Exception {
        System.load(args[0]);
        Throwable cause=new IllegalStateException("CAUSE_MARKER ñ 📺");
        check(Log.e("Throwables","MULTILINE_MESSAGE\nSECOND_MESSAGE_LINE",new RuntimeException("OUTER_MARKER",cause))>0,"Throwable write");
        check(Log.e("Throwables","NETWORK_MESSAGE_VISIBLE",new RuntimeException("NETWORK_WRAPPER_SUPPRESSED",new UnknownHostException("NETWORK_CAUSE_SUPPRESSED")))>0,"Network message write");
        check(Log.e("Throwables","DEAD_SYSTEM_MESSAGE",new DeadSystemException())>0,"Dead system message write");
        String longMessage="LONG_BEGIN:"+new String(new char[12000]).replace('\0','x')+":LONG_END";
        check(Log.e("Throwables",longMessage,(Throwable)null)>0,"Long line write");
        System.out.println("AOSP_THROWABLE_LOG_OK");
    }
}
