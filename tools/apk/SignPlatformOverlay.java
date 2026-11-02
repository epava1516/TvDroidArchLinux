import com.android.apksig.ApkSigner;
import com.android.apksig.ApkVerifier;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.KeyStore;
import java.security.PrivateKey;
import java.security.MessageDigest;
import java.security.cert.X509Certificate;
import java.util.Collections;

/** Build-time original apksig API; private signing material stays outside Git. */
public final class SignPlatformOverlay {
    public static void main(String[] args) throws Exception {
        char[] password=Files.readString(Path.of(args[1])).strip().toCharArray();
        KeyStore store=KeyStore.getInstance("PKCS12");
        try(java.io.InputStream input=Files.newInputStream(Path.of(args[0]))) {
            store.load(input,password);
        }
        PrivateKey key=(PrivateKey)store.getKey("archtv-overlay",password);
        X509Certificate cert=(X509Certificate)store.getCertificate("archtv-overlay");
        java.util.Arrays.fill(password,'\0');
        ApkSigner.SignerConfig config=new ApkSigner.SignerConfig.Builder("archtv-overlay",key,
                Collections.singletonList(cert)).build();
        new ApkSigner.Builder(Collections.singletonList(config))
                .setInputApk(new File(args[2])).setOutputApk(new File(args[3]))
                .setV1SigningEnabled(false).setV2SigningEnabled(true)
                .setV3SigningEnabled(true).setV4SigningEnabled(false).build().sign();
        ApkVerifier.Result result=new ApkVerifier.Builder(new File(args[3])).build().verify();
        if(!result.isVerified() || !result.isVerifiedUsingV3Scheme())
            throw new IllegalStateException("Original apksig verification failed: verified="+result.isVerified()+" v2="+result.isVerifiedUsingV2Scheme()+" v3="+result.isVerifiedUsingV3Scheme()+" errors="+result.getErrors());
        StringBuilder digest=new StringBuilder();
        for(byte b:MessageDigest.getInstance("SHA-256").digest(cert.getEncoded()))
            digest.append(String.format("%02x",b&255));
        System.out.println("ORIGINAL_APKSIG_VERIFIED v2_checked="+result.isVerifiedUsingV2Scheme()+" v3_checked="+result.isVerifiedUsingV3Scheme()+" signer_sha256="+digest);
    }
}
