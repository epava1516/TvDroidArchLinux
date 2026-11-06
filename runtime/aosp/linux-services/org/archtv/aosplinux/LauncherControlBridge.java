package org.archtv.aosplinux;

import java.io.*;
import java.lang.reflect.*;
import java.nio.ByteBuffer;
import java.nio.charset.*;
import java.util.*;

/** Trusted Linux launcher adapter, not a package/activity implementation.
 * Original PMS supplies the catalog and original Context/ATMS starts activities.
 * This endpoint has no install, permission, shell, path or cross-user operation.
 */
final class LauncherControlBridge {
    private static final int MAGIC=0x41544c31, MAX_REQUEST=1024, MAX_RESPONSE=262144;
    private static final String LAUNCHER="android.intent.category.LAUNCHER";
    private static final String LEANBACK="android.intent.category.LEANBACK_LAUNCHER";
    private final Object context,pm;
    private String lastObservedCatalog;
    private final Class<?> intentType,pmType,componentType;
    private static Object call(Object receiver,String name,Class<?>[] types,Object... args) throws Exception {
        Class<?> type=receiver instanceof Class ? (Class<?>)receiver:receiver.getClass();
        // ContextImpl is package-private: use its public Context ancestor,
        // never setAccessible or suppress original API access checks.
        while(!Modifier.isPublic(type.getModifiers()))type=type.getSuperclass();
        try{return type.getMethod(name,types).invoke(receiver instanceof Class?null:receiver,args);}
        catch(InvocationTargetException e){
            if(e.getCause() instanceof SecurityException)throw (SecurityException)e.getCause();
            throw new Exception("Original "+name+" failed",e.getCause());
        }
    }
    private LauncherControlBridge(Object context) throws Exception {
        this.context=context;
        if((Integer)call(context,"getUserId",new Class<?>[0])!=0)
            throw new SecurityException("Launcher adapter requires actual user0 context");
        pm=call(context,"getPackageManager",new Class<?>[0]);
        pmType=Class.forName("android.content.pm.PackageManager");
        intentType=Class.forName("android.content.Intent");
        componentType=Class.forName("android.content.ComponentName");
    }
    private Object intent(String category) throws Exception {
        Object intent=intentType.getConstructor(String.class).newInstance("android.intent.action.MAIN");
        call(intent,"addCategory",new Class<?>[]{String.class},category);
        return intent;
    }
    private static final class Entry {
        final String component,label,category;
        Entry(String component,String label,String category){this.component=component;this.label=label;this.category=category;}
    }
    private SortedMap<String,Entry> catalog() throws Exception {
        SortedMap<String,Entry> entries=new TreeMap<>();
        // Prefer the original TV launcher activity when a component advertises
        // both categories. No synthetic entry for the current test package.
        for(String category:new String[]{LEANBACK,LAUNCHER}) {
            List<?> resolved=(List<?>)call(pm,"queryIntentActivities",new Class<?>[]{intentType,int.class},intent(category),0);
            for(Object resolution:resolved) {
                Object activity=resolution.getClass().getField("activityInfo").get(resolution);
                // Flags0 leaves component/application enabled-state resolution
                // to original PMS, including runtime overrides of manifest
                // defaults. Do not reproduce that logic from ActivityInfo bits.
                if(!activity.getClass().getField("exported").getBoolean(activity))continue;
                String pkg=(String)activity.getClass().getField("packageName").get(activity);
                String cls=(String)activity.getClass().getField("name").get(activity);
                Object component=componentType.getConstructor(String.class,String.class).newInstance(pkg,cls);
                String flat=(String)call(component,"flattenToString",new Class<?>[0]);
                CharSequence label=(CharSequence)call(resolution,"loadLabel",new Class<?>[]{pmType},pm);
                entries.putIfAbsent(flat,new Entry(flat,label==null?pkg:label.toString(),category));
                if(entries.size()>512)throw new IOException("Catalog exceeds scoped512-entry bound; not a complete result");
            }
        }
        return entries;
    }
    private static void string(DataOutputStream out,String text,int maximum) throws IOException {
        byte[] bytes=text.getBytes(StandardCharsets.UTF_8);
        if(bytes.length>maximum)throw new IOException("Original string exceeds protocol bound");
        out.writeInt(bytes.length);out.write(bytes);
    }
    private byte[] list() throws Exception {
        SortedMap<String,Entry> entries=catalog();
        ByteArrayOutputStream bytes=new ByteArrayOutputStream();DataOutputStream out=new DataOutputStream(bytes);
        out.writeInt(entries.size());
        for(Entry e:entries.values()){string(out,e.component,1024);string(out,e.label,4096);string(out,e.category,128);}
        if(bytes.size()>MAX_RESPONSE)throw new IOException("Catalog exceeds response bound; not a complete result");
        // Explicit known-media integration observation only. These are the
        // actual original PMS entries returned on the existing private wire;
        // no test-package substitution, enable-state override or new inventory.
        if ("1".equals(System.getenv("ARCHTV_OBSERVE_LAUNCHER_CATALOG"))) {
            String snapshot=Base64.getEncoder().encodeToString(bytes.toByteArray());
            if (!snapshot.equals(lastObservedCatalog)) {
                lastObservedCatalog=snapshot;
                int sampled=0,index=0;
                for (Entry e:entries.values()) {
                    byte[] component=e.component.getBytes(StandardCharsets.UTF_8);
                    byte[] label=e.label.getBytes(StandardCharsets.UTF_8);
                    byte[] category=e.category.getBytes(StandardCharsets.UTF_8);
                    // Keep each original logcat line below its transport bound.
                    // Oversized fields stay in the real RPC, unsampled here.
                    if(component.length<=256 && label.length<=256 && category.length<=128) {
                        System.err.println("LAUNCHER_ORIGINAL_CATALOG_ENTRY index="+index
                                +" component64="+Base64.getEncoder().encodeToString(component)
                                +" label64="+Base64.getEncoder().encodeToString(label)
                                +" category64="+Base64.getEncoder().encodeToString(category)
                                +" NOT_APP_COMPATIBILITY");
                        sampled++;
                    }
                    index++;
                }
                System.err.println("LAUNCHER_ORIGINAL_CATALOG_OBSERVATION_END total="+entries.size()
                        +" sampled="+sampled+" NOT_INVENTORY_OR_LAUNCH_ACCEPTANCE");
            }
        }
        System.err.println("LAUNCHER_ORIGINAL_CATALOG_RETURNED count="+entries.size()+" user=0 NOT_APP_COMPATIBILITY");
        return bytes.toByteArray();
    }
    private void launcherUserActivity() throws Exception {
        // This is the already authenticated Linux Home launch request, not a
        // catalog poll or synthetic keepalive. Original PowerManager owns wake,
        // display-group policy and permission checks; never hold a wake lock or
        // change the original screen timeout to make a launch appear visible.
        Object power=call(context,"getSystemService",new Class<?>[]{String.class},"power");
        if(power==null)throw new IOException("Original PowerManager unavailable");
        Class<?> powerType=Class.forName("android.os.PowerManager");
        long when=(Long)call(Class.forName("android.os.SystemClock"),"uptimeMillis",new Class<?>[0]);
        boolean before=(Boolean)call(power,"isInteractive",new Class<?>[0]);
        if(!before)call(power,"wakeUp",new Class<?>[]{long.class,int.class,String.class},when,
                powerType.getField("WAKE_REASON_APPLICATION").getInt(null),"archtv:linux-home-launch");
        call(power,"userActivity",new Class<?>[]{long.class,int.class,int.class},when,
                powerType.getField("USER_ACTIVITY_EVENT_OTHER").getInt(null),0);
        boolean after=(Boolean)call(power,"isInteractive",new Class<?>[0]);
        System.err.println("LAUNCHER_ORIGINAL_POWER_REQUEST_RETURNED beforeInteractive="+before
                +" afterInteractive="+after+" uptimeMillis="+when+" NOT_DISPLAY_OR_LIFECYCLE_ACCEPTANCE");
    }
    private byte[] launch(String component) throws Exception {
        // Resolve current original PMS state again. An old catalog is never a
        // grant to launch an arbitrary component or a disabled/uninstalled app.
        Entry entry=catalog().get(component);
        if(entry==null)throw new SecurityException("Component absent from current exported enabled launcher catalog");
        Object target=call(componentType,"unflattenFromString",new Class<?>[]{String.class},entry.component);
        if(target==null)throw new IOException("Original ComponentName rejected catalog entry");
        Object intent=intent(entry.category);
        call(intent,"setComponent",new Class<?>[]{componentType},target);
        int flags=intentType.getField("FLAG_ACTIVITY_NEW_TASK").getInt(null)
            |intentType.getField("FLAG_ACTIVITY_RESET_TASK_IF_NEEDED").getInt(null);
        call(intent,"addFlags",new Class<?>[]{int.class},flags);
        // The actual Context is user0. Its standard startActivity path uses
        // Instrumentation's original start-result checks. ContextImpl's hidden
        // startActivityAsUser overload discards ATMS's integer result instead.
        launcherUserActivity();
        call(context,"startActivity",new Class<?>[]{intentType},intent);
        System.err.println("LAUNCHER_ORIGINAL_START_REQUEST_RETURNED component="+entry.component+" user=0 NOT_FRAME_OR_LIFECYCLE_ACCEPTANCE");
        return "original start request returned; presentation unverified".getBytes(StandardCharsets.UTF_8);
    }
    private static String utf8(byte[] bytes) throws CharacterCodingException {
        return StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
            .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes)).toString();
    }
    private void connection(Object socket) throws Exception {
        Object creds=call(socket,"getPeerCredentials",new Class<?>[0]);
        int uid=(Integer)call(creds,"getUid",new Class<?>[0]);
        FileDescriptor fd=(FileDescriptor)call(socket,"getFileDescriptor",new Class<?>[0]);
        String peer=(String)call(Class.forName("android.os.SELinux"),"getPeerContext",new Class<?>[]{FileDescriptor.class},fd);
        if(uid!=1000 || !"u:r:hal_graphics_composer_default:s0".equals(peer)) {
            System.err.println("LAUNCHER_CONTROL_PEER_REJECTED uid="+uid+" context="+peer);return;
        }
        // Finite idle/partial-frame/write bounds; clients may reconnect. Never
        // retry a launch on disconnect: its effect could already have occurred.
        call(socket,"setSoTimeout",new Class<?>[]{int.class},3000);
        DataInputStream in=new DataInputStream((InputStream)call(socket,"getInputStream",new Class<?>[0]));
        DataOutputStream out=new DataOutputStream((OutputStream)call(socket,"getOutputStream",new Class<?>[0]));
        long last=0;
        for(int requests=0;requests<64;requests++) {
            int magic=in.readInt(),sequence=in.readInt(),op=in.readInt(),length=in.readInt();
            long serial=Integer.toUnsignedLong(sequence);
            if(magic!=MAGIC || serial<=last || length<0 || length>MAX_REQUEST
                || (op!=1 && op!=2) || (op==1 && length!=0) || (op==2 && length==0))
                throw new IOException("Invalid launcher request");
            last=serial;byte[] request=new byte[length];in.readFully(request);
            int status=0;byte[] response;
            try {response=op==1?list():launch(utf8(request));}
            catch(Exception error) {
                status=error instanceof SecurityException?1:2;
                System.err.println("LAUNCHER_ORIGINAL_OPERATION_FAILED op="+op+" "+error);
                error.printStackTrace(System.err);
                response=("Original operation failed: "+error.getClass().getSimpleName()).getBytes(StandardCharsets.UTF_8);
            }
            out.writeInt(MAGIC);out.writeInt(sequence);out.writeInt(status);out.writeInt(response.length);out.write(response);out.flush();
        }
    }
    static void start(Object context) throws Exception {
        LauncherControlBridge bridge=new LauncherControlBridge(context);
        Object server=WaylandInputBridge.createServer("archtv-launcher-control-v1");
        Thread worker=new Thread(()->{
            for(;;){Object socket=null;
                try {socket=call(server,"accept",new Class<?>[0]);bridge.connection(socket);}
                catch(EOFException closed){}
                catch(Exception failure){System.err.println("LAUNCHER_CONTROL_CONNECTION_ENDED "+failure);}
                finally{if(socket!=null)try{call(socket,"close",new Class<?>[0]);}catch(Exception ignored){}}
            }
        },"linux-original-launcher");worker.setDaemon(true);worker.start();
        System.err.println("LAUNCHER_CONTROL_LISTENING user=0 NOT_RUNTIME_OR_LAUNCH_ACCEPTANCE");
    }
}
