import java.io.File;
import java.security.MessageDigest;
import java.security.cert.X509Certificate;
import com.android.apksig.ApkVerifier;
public final class VerifyMarkor {
 public static void main(String[] args) throws Exception {
  ApkVerifier.Result r=new ApkVerifier.Builder(new File(args[0]))
    .setMinCheckedPlatformVersion(36).setMaxCheckedPlatformVersion(36).build().verify();
  System.out.println("AOSP_APK_VERIFIER verified="+r.isVerified()+" v1="+r.isVerifiedUsingV1Scheme()+" v2="+r.isVerifiedUsingV2Scheme());
  for(X509Certificate c:r.getSignerCertificates()) {
   byte[] h=MessageDigest.getInstance("SHA-256").digest(c.getEncoded());StringBuilder s=new StringBuilder();
   for(byte b:h)s.append(String.format("%02x",b));System.out.println("SIGNER_CERT_SHA256 "+s);
  }
  for(Object e:r.getErrors())System.out.println("ERROR "+e);
  for(ApkVerifier.Result.V2SchemeSignerInfo s:r.getV2SchemeSigners())
   for(Object e:s.getErrors())System.out.println("V2_ERROR "+e);
  if(!r.isVerified())System.exit(1);
 }
}
