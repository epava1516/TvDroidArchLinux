package org.archtv.keystoreprobe;

import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyInfo;
import android.security.keystore.KeyProperties;
import android.security.keystore.StrongBoxUnavailableException;
import java.nio.file.*;
import java.security.*;
import java.util.Arrays;
import javax.crypto.*;
import javax.crypto.spec.GCMParameterSpec;

/** Original JCA provider integration; no Android implementations in this fixture. */
public final class OriginalJavaProviderProbe {
    private static final String ALIAS = "archtv-original-java-aes";
    private static final byte[] MESSAGE = "original Java Keystore provider".getBytes(java.nio.charset.StandardCharsets.UTF_8);
    private static void result(String value) {
        // RuntimeInit redirects System.out to Android log; preserve the actual
        // client output descriptor captured by the original shell redirection.
        new java.io.PrintStream(new java.io.FileOutputStream(java.io.FileDescriptor.out), true).println(value);
    }
    private static void require(boolean value, String error) { if (!value) throw new AssertionError(error); }
    private static KeyGenParameterSpec spec(boolean hardware) {
        return new KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256).setUserAuthenticationRequired(false).setIsStrongBoxBacked(hardware).build();
    }
    private static void info(SecretKey key) throws Exception {
        KeyInfo info = (KeyInfo) SecretKeyFactory.getInstance("AES", "AndroidKeyStore").getKeySpec(key, KeyInfo.class);
        // Installed compiler SDK predates this API; resolve the real boot implementation.
        int level=((Integer)KeyInfo.class.getMethod("getSecurityLevel").invoke(info)).intValue();
        int software=KeyProperties.class.getField("SECURITY_LEVEL_SOFTWARE").getInt(null);
        require(level == software, "incorrect actual security level");
        require(!info.isInsideSecureHardware() && !info.isUserAuthenticationRequired(), "false protection metadata");
    }
    public static void main(String[] args) throws Exception {
        require(args.length == 2, "write|read ciphertext-file");
        Class<?> provider = Class.forName("android.security.keystore2.AndroidKeyStoreProvider");
        provider.getMethod("install").invoke(null);
        require(provider.getClassLoader() == Class.forName("android.security.keystore2.AndroidKeyStoreKeyGeneratorSpi").getClassLoader(), "provider loader split");
        Path path=Paths.get(args[1]);
        KeyStore store=KeyStore.getInstance("AndroidKeyStore");store.load(null);
        if (args[0].equals("write")) {
            KeyGenerator hardware=KeyGenerator.getInstance("AES", "AndroidKeyStore");hardware.init(spec(true));
            boolean rejected=false;
            try { hardware.generateKey(); } catch (StrongBoxUnavailableException expected) { rejected=true; }
            require(rejected,"StrongBox unavailable request was accepted");
            KeyGenerator generator=KeyGenerator.getInstance("AES", "AndroidKeyStore");generator.init(spec(false));
            SecretKey key=generator.generateKey();info(key);
            Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");cipher.init(Cipher.ENCRYPT_MODE,key);
            byte[] nonce=cipher.getIV(), encrypted=cipher.doFinal(MESSAGE);
            require(nonce.length==12,"nonce length");
            byte[] data=new byte[nonce.length+encrypted.length];System.arraycopy(nonce,0,data,0,12);System.arraycopy(encrypted,0,data,12,encrypted.length);
            Files.write(path,data,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
            result("ORIGINAL_JCA_ENCRYPTED SOFTWARE strongbox_rejected=1 pid="+android.os.Process.myPid()+" NOT_APK_OR_MAC_ACCEPTANCE");
        } else {
            require(args[0].equals("read"),"unknown mode");
            SecretKey key=(SecretKey)store.getKey(ALIAS,null);require(key!=null,"key missing after client restart");info(key);
            byte[] data=Files.readAllBytes(path);require(data.length>28 && data.length<4096,"cipher size");
            Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");cipher.init(Cipher.DECRYPT_MODE,key,new GCMParameterSpec(128,Arrays.copyOf(data,12)));
            require(Arrays.equals(MESSAGE,cipher.doFinal(Arrays.copyOfRange(data,12,data.length))),"plaintext mismatch");
            data[data.length-1]^=1;cipher.init(Cipher.DECRYPT_MODE,key,new GCMParameterSpec(128,Arrays.copyOf(data,12)));
            boolean rejected=false;try { cipher.doFinal(Arrays.copyOfRange(data,12,data.length)); } catch (AEADBadTagException expected) { rejected=true; }
            require(rejected,"tampered tag accepted");store.deleteEntry(ALIAS);require(!store.containsAlias(ALIAS),"deleted key retained");
            result("ORIGINAL_JCA_REOPENED SOFTWARE tamper_rejected=1 deleted=1 pid="+android.os.Process.myPid()+" NOT_APK_OR_MAC_ACCEPTANCE");
        }
    }
}
