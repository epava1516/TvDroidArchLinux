package org.archtv.aosplinux;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Properties;

/** Read the live Rust Wayland host snapshot; this does not create windows or render. */
final class WindowPolicyState {
    static final class Snapshot {
        int initialWidth,initialHeight,width,height,density,ownerPid;
        long ownerStart,generation;
        boolean navigationBar,blast;
        float animatorScale;
    }
    private final Path path;
    private final Snapshot initial;
    private long generation;
    WindowPolicyState(Path path) throws IOException {
        this.path=path;initial=load(path);generation=initial.generation;
    }
    synchronized Snapshot read() throws IOException {
        Snapshot current=load(path);
        if (current.ownerPid!=initial.ownerPid || current.ownerStart!=initial.ownerStart
                || current.initialWidth!=initial.initialWidth || current.initialHeight!=initial.initialHeight
                || current.generation<generation) throw new IOException("Window provider changed or regressed");
        generation=current.generation;return current;
    }
    private static byte[] bytes(Path path,int maximum) throws IOException {
        try (InputStream input=Files.newInputStream(path)) {
            ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buffer=new byte[512];int count;
            while ((count=input.read(buffer))!=-1) {
                if (out.size()+count>maximum) throw new IOException("Window provider record exceeds budget");
                out.write(buffer,0,count);
            }
            return out.toByteArray();
        }
    }
    private static Snapshot load(Path path) throws IOException {
        try {
            Properties p=new Properties();p.load(new ByteArrayInputStream(bytes(path,4096)));
            HashSet<String> expected=new HashSet<String>(Arrays.asList("version","source","owner_pid","owner_start_ticks",
                "generation","initial_width","initial_height","width","height","density","navigation_bar","blast","animator_scale"));
            if (!p.stringPropertyNames().equals(expected) || !"1".equals(p.getProperty("version"))
                    || !"wayland-shm".equals(p.getProperty("source"))) throw new IOException("Unsupported window provider schema");
            Snapshot s=new Snapshot();s.ownerPid=Integer.parseInt(p.getProperty("owner_pid"));
            s.ownerStart=Long.parseLong(p.getProperty("owner_start_ticks"));s.generation=Long.parseLong(p.getProperty("generation"));
            s.initialWidth=Integer.parseInt(p.getProperty("initial_width"));s.initialHeight=Integer.parseInt(p.getProperty("initial_height"));
            s.width=Integer.parseInt(p.getProperty("width"));s.height=Integer.parseInt(p.getProperty("height"));
            s.density=Integer.parseInt(p.getProperty("density"));s.animatorScale=Float.parseFloat(p.getProperty("animator_scale"));
            s.navigationBar=bool(p,"navigation_bar");s.blast=bool(p,"blast");
            if (s.ownerPid<=1 || s.ownerStart<=0 || s.generation<=0 || s.width<1 || s.width>3840 || s.height<1 || s.height>2160
                    || s.initialWidth<1 || s.initialWidth>3840 || s.initialHeight<1 || s.initialHeight>2160 || s.density!=160
                    || Float.isNaN(s.animatorScale) || Float.isInfinite(s.animatorScale) || s.animatorScale<0 || s.animatorScale>10)
                throw new IOException("Invalid window provider values");
            String stat=new String(bytes(Paths.get("/proc/"+s.ownerPid+"/stat"),8192),StandardCharsets.US_ASCII);
            String[] fields=stat.substring(stat.lastIndexOf(')')+1).trim().split("\\s+");
            if (fields.length<20 || fields[0].equals("Z") || fields[0].equals("X") || Long.parseLong(fields[19])!=s.ownerStart)
                throw new IOException("Window provider is no longer alive");
            return s;
        } catch (IllegalArgumentException | IndexOutOfBoundsException error) { throw new IOException("Invalid window provider record",error); }
    }
    private static boolean bool(Properties p,String key) throws IOException {
        if ("true".equals(p.getProperty(key))) return true;
        if ("false".equals(p.getProperty(key))) return false;
        throw new IOException("Invalid window boolean: "+key);
    }
}
