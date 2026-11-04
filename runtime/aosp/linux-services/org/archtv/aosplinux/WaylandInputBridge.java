package org.archtv.aosplinux;

import java.io.*;
import java.lang.reflect.*;
import java.util.*;

/** Private Linux seat gateway. Original InputManager owns permission checks,
 * focus, window targeting and dispatch; no APK callbacks or widget emulation. */
final class WaylandInputBridge {
    private final Object input;
    private final Class<?> eventType, keyType, motionType;
    private final Map<Integer, Long> held = new HashMap<>();
    private long touchDown;
    private boolean touching;
    private int lastX, lastY;
    private int meta;
    private WaylandInputBridge(Object input) throws Exception {
        this.input=input;
        eventType=Class.forName("android.view.InputEvent");
        keyType=Class.forName("android.view.KeyEvent");
        motionType=Class.forName("android.view.MotionEvent");
    }
    private static Object invoke(Object receiver,String method,Class<?>[] types,Object... values) throws Exception {
        Class<?> type=receiver instanceof Class ? (Class<?>)receiver:receiver.getClass();
        try{return type.getMethod(method,types).invoke(receiver instanceof Class?null:receiver,values);}
        catch(InvocationTargetException e){throw new Exception("Original "+method+" failed",e.getCause());}
    }
    private long now() throws Exception {
        return (Long)invoke(Class.forName("android.os.SystemClock"),"uptimeMillis",new Class<?>[0]);
    }
    private boolean dispatch(Object event) throws Exception {
        invoke(event,"setDisplayId",new Class<?>[]{int.class},0);
        try {
            // WAIT_FOR_FINISH, as original InputShellCommand: do not ACK ahead
            // of window/IME delivery. Original permission/target checks stay intact.
            return (Boolean)invoke(input,"injectInputEvent",new Class<?>[]{eventType,int.class},event,2);
        } finally {if(motionType.isInstance(event))invoke(event,"recycle",new Class<?>[0]);}
    }
    private boolean key(int code,int action,int scan,int state) throws Exception {
        long when=now();Long down=held.get(code);
        if(action==0){if(down!=null)throw new IOException("Duplicate key down");held.put(code,when);down=when;}
        else {if(down==null)throw new IOException("Unmatched key up");held.remove(code);}
        meta=state;
        Object event=keyType.getConstructor(long.class,long.class,int.class,int.class,int.class,int.class,int.class,int.class,int.class,int.class)
            .newInstance(down,when,action,code,0,state,-1,scan,0,0x101);
        return dispatch(event);
    }
    private boolean touch(int action,int x,int y,int state) throws Exception {
        long when=now();
        if(action==0){if(touching)throw new IOException("Duplicate touch down");touchDown=when;touching=true;}
        else if(!touching)throw new IOException("Unmatched touch");
        lastX=x;lastY=y;
        // A single virtual touchscreen translated from the host pointer. This
        // does not claim native mouse hover/scroll, multitouch or device enumeration.
        Object event=invoke(motionType,"obtain",new Class<?>[]{long.class,long.class,int.class,float.class,float.class,int.class},touchDown,when,action,x/1000f,y/1000f,state);
        invoke(event,"setSource",new Class<?>[]{int.class},0x1002);
        boolean accepted=dispatch(event);
        if(action==1 || action==3)touching=false;
        return accepted;
    }
    private void release() {
        for(int code:new ArrayList<>(held.keySet()))try{key(code,1,0,0);}catch(Exception e){System.err.println("WAYLAND_INPUT_RELEASE_FAILED "+e);}
        if(touching)try{touch(3,lastX,lastY,0);}catch(Exception e){System.err.println("WAYLAND_INPUT_CANCEL_FAILED "+e);}
        held.clear();touching=false;meta=0;
    }
    private void connection(Object socket) throws Exception {
        Object creds=invoke(socket,"getPeerCredentials",new Class<?>[0]);
        int uid=(Integer)invoke(creds,"getUid",new Class<?>[0]);
        int pid=(Integer)invoke(creds,"getPid",new Class<?>[0]);
        FileDescriptor fd=(FileDescriptor)invoke(socket,"getFileDescriptor",new Class<?>[0]);
        String context=(String)invoke(Class.forName("android.os.SELinux"),"getPeerContext",new Class<?>[]{FileDescriptor.class},fd);
        if(uid!=1000 || !"u:r:hal_graphics_composer_default:s0".equals(context)){
            System.err.println("WAYLAND_INPUT_PEER_REJECTED pid="+pid+" uid="+uid+" context="+context);return;
        }
        System.err.println("WAYLAND_INPUT_PEER_AUTHENTICATED pid="+pid+" uid="+uid+" context="+context);
        invoke(socket,"setSoTimeout",new Class<?>[]{int.class},3000);
        DataInputStream stream=new DataInputStream((InputStream)invoke(socket,"getInputStream",new Class<?>[0]));
        DataOutputStream output=new DataOutputStream((OutputStream)invoke(socket,"getOutputStream",new Class<?>[0]));
        long sequence=0;
        int maximum=(Integer)invoke(keyType,"getMaxKeyCode",new Class<?>[0]);
        try {
            for(;;){
                int magic;
                invoke(socket,"setSoTimeout",new Class<?>[]{int.class},0);
                int first=stream.read();if(first<0)throw new EOFException();
                invoke(socket,"setSoTimeout",new Class<?>[]{int.class},3000);
                magic=(first<<24)|(stream.readUnsignedByte()<<16)|(stream.readUnsignedByte()<<8)|stream.readUnsignedByte();
                // Remaining packet must arrive within the socket bound; partial
                // frames cannot indefinitely own the gateway.
                int type=stream.readInt();long seq=Integer.toUnsignedLong(stream.readInt());
                int code=stream.readInt(),action=stream.readInt(),state=stream.readInt(),scan=stream.readInt(),x=stream.readInt(),y=stream.readInt(),repeat=stream.readInt();
                if(magic!=0x41544931 || seq<=sequence || repeat!=0)throw new IOException("Invalid input packet");
                sequence=seq;boolean accepted;
                if(type==1 && code>0 && code<=maximum && (action==0 || action==1) && scan>=0 && scan<=767)accepted=key(code,action,scan,state);
                else if(type==2 && (action==0 || action==1 || action==2 || action==3) && x>=0 && y>=0 && x<=8192000 && y<=8192000)accepted=touch(action,x,y,state);
                else throw new IOException("Unsupported input contract");
                output.writeInt((int)seq);output.writeInt(accepted?1:0);output.flush();
                System.err.println("WAYLAND_INPUT_ORIGINAL_DISPATCH seq="+seq+" type="+type+" code="+code+" action="+action+" accepted="+accepted);
            }
        }finally{release();}
    }
    private void serve(Object server) {
        for(;;){Object socket=null;
            try {socket=invoke(server,"accept",new Class<?>[0]);connection(socket);}
            catch(EOFException closed){System.err.println("WAYLAND_INPUT_PEER_CLOSED");}
            catch(Exception failure){System.err.println("WAYLAND_INPUT_CONNECTION_FAILED "+failure);}
            finally{if(socket!=null)try{invoke(socket,"close",new Class<?>[0]);}catch(Exception ignored){}}
        }
    }
    private static void verifyRejectedPeer() throws Exception {
        Object client=Class.forName("android.net.LocalSocket").getConstructor().newInstance();
        try {
            Object address=Class.forName("android.net.LocalSocketAddress").getConstructor(String.class).newInstance("archtv-wayland-input-v1");
            invoke(client,"connect",new Class<?>[]{address.getClass()},address);
            invoke(client,"setSoTimeout",new Class<?>[]{int.class},3000);
            int result=((InputStream)invoke(client,"getInputStream",new Class<?>[0])).read();
            if(result!=-1)throw new SecurityException("Gateway accepted non-composer peer");
            System.err.println("WAYLAND_INPUT_NEGATIVE_PEER_CLOSED actual_uid=1000 actual_domain=system_server NOT_APP_UID_OR_MAC_ACCEPTANCE");
        }finally{invoke(client,"close",new Class<?>[0]);}
    }
    private static Object createServer() throws Exception {
        // Linux's per-thread socket-create attribute labels this one endpoint.
        // Restore it even if the original LocalServerSocket constructor fails;
        // never change system_server's process identity or all of its sockets.
        final String attribute="/proc/thread-self/attr/sockcreate";
        final String context="u:object_r:archtv_input_channel:s0";
        byte[] previous;
        try(FileInputStream file=new FileInputStream(attribute)){
            ByteArrayOutputStream saved=new ByteArrayOutputStream();
            byte[] buffer=new byte[256];int count;
            while((count=file.read(buffer))!=-1){
                if(count==0 || saved.size()+count>4096)throw new IOException("Invalid socket-create context length");
                saved.write(buffer,0,count);
            }
            previous=saved.toByteArray();
        }
        Object server=null;
        try {
            try(FileOutputStream file=new FileOutputStream(attribute)){
                file.write((context+'\0').getBytes(java.nio.charset.StandardCharsets.UTF_8));
            }
            server=Class.forName("android.net.LocalServerSocket").getConstructor(String.class).newInstance("archtv-wayland-input-v1");
        }finally{
            try(FileOutputStream file=new FileOutputStream(attribute)){
                if(previous.length==0)file.write(0);else file.write(previous);
            }catch(Exception failure){
                if(server!=null)invoke(server,"close",new Class<?>[0]);
                throw failure;
            }
        }
        return server;
    }
    static void start(Object input) throws Exception {
        WaylandInputBridge bridge=new WaylandInputBridge(input);
        // Abstract sockets are scoped by the cohort's private network namespace.
        // Both peers also verify kernel-provided UID and SELinux context.
        Object server=createServer();
        Thread worker=new Thread(()->bridge.serve(server),"linux-wayland-input");worker.setDaemon(true);worker.start();
        System.err.println("WAYLAND_INPUT_GATEWAY_LISTENING NOT_APK_INPUT_ACCEPTANCE");
        verifyRejectedPeer();
    }
}
