package org.archtv.aosplinux;

import android.os.DeadObjectException;
import android.os.IBinder;
import android.os.IInterface;
import android.os.Parcel;
import android.os.ResultReceiver;
import android.os.ShellCallback;
import java.io.FileDescriptor;
import java.util.ArrayList;
import java.util.NoSuchElementException;
import java.util.Objects;

/** Local service endpoint for the original Binder interfaces; no Binder IPC transport. */
public abstract class LocalServiceBinder implements IBinder, IInterface, AutoCloseable {
    private final String descriptor;
    private boolean alive = true;
    private final ArrayList<DeathRecipient> recipients = new ArrayList<DeathRecipient>();
    protected LocalServiceBinder(String descriptor) {
        this.descriptor = Objects.requireNonNull(descriptor);
        if (descriptor.isEmpty()) throw new IllegalArgumentException("Empty service descriptor");
    }
    private void requireAlive() throws DeadObjectException {
        if (!alive) throw new DeadObjectException();
    }
    @Override public final IBinder asBinder() { return this; }
    @Override public final synchronized String getInterfaceDescriptor() throws DeadObjectException {
        requireAlive();return descriptor;
    }
    @Override public final synchronized boolean pingBinder() { return alive; }
    @Override public final synchronized boolean isBinderAlive() { return alive; }
    @Override public final synchronized IInterface queryLocalInterface(String requested) {
        return alive && descriptor.equals(requested) ? this : null;
    }
    @Override public final synchronized IBinder getExtension() throws DeadObjectException {
        requireAlive();return null;
    }
    @Override public final void dump(FileDescriptor fd,String[] args) {
        throw new UnsupportedOperationException("Local service dump not implemented");
    }
    @Override public final void dumpAsync(FileDescriptor fd,String[] args) {
        throw new UnsupportedOperationException("Local service dumpAsync not implemented");
    }
    @Override public final void shellCommand(FileDescriptor in,FileDescriptor out,FileDescriptor err,
            String[] args,ShellCallback callback,ResultReceiver result) {
        throw new UnsupportedOperationException("Local service shellCommand not implemented");
    }
    @Override public final boolean transact(int code,Parcel input,Parcel output,int flags) {
        throw new UnsupportedOperationException("Local service Binder IPC transact not implemented");
    }
    @Override public final synchronized void linkToDeath(DeathRecipient recipient,int flags) throws DeadObjectException {
        if (flags!=0) throw new UnsupportedOperationException("Local service death flags");
        requireAlive();recipients.add(Objects.requireNonNull(recipient));
    }
    @Override public final synchronized boolean unlinkToDeath(DeathRecipient recipient,int flags) {
        if (flags!=0) throw new UnsupportedOperationException("Local service death flags");
        if (!alive) return false;
        if (!recipients.remove(recipient)) throw new NoSuchElementException("Death recipient not registered");
        return true;
    }
    @Override public final void close() {
        ArrayList<DeathRecipient> notify;
        synchronized (this) {
            if (!alive) return;
            alive=false;notify=new ArrayList<DeathRecipient>(recipients);recipients.clear();
        }
        RuntimeException failure=null;
        for (DeathRecipient recipient:notify) {
            try { recipient.binderDied(); }
            catch (RuntimeException error) {
                if (failure==null) failure=error;else failure.addSuppressed(error);
            }
        }
        if (failure!=null) throw failure;
    }
}
