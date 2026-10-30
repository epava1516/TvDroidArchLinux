package org.archtv.apkruntime;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

/** Bounded default-configuration plain string resource reader, based on ResourceTypes.h. */
public final class ApkResources {
    private final ByteBuffer bytes;
    private String[] strings;
    private final Map<Integer, int[]> values = new HashMap<Integer, int[]>();
    public ApkResources(Path apk) throws Exception {
        byte[] data;
        try (ZipFile archive = new ZipFile(apk.toFile())) {
            ZipEntry entry = archive.getEntry("resources.arsc");
            if (entry == null || entry.getSize() > 16*1024*1024) throw bad("Missing or oversized resources.arsc");
            try (InputStream input = archive.getInputStream(entry);
                 ByteArrayOutputStream output = new ByteArrayOutputStream()) {
                byte[] block = new byte[8192];
                int count;
                while ((count = input.read(block)) != -1) {
                    if (output.size()+count > 16*1024*1024) throw bad("Resources exceed budget");
                    output.write(block, 0, count);
                }
                data = output.toByteArray();
            }
        }
        bytes = ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
        int end = chunkEnd(0, data.length);
        if (u16(0) != 2 || end != data.length || u16(2) < 12) throw bad("Invalid resource table");
        for (int position = u16(2); position < end;) {
            int next = chunkEnd(position, end);
            if (u16(position) == 1) {
                if (strings != null) throw bad("Duplicate global string pool");
                strings = stringPool(position, next);
            } else if (u16(position) == 0x200) {
                if (strings == null) throw bad("Package precedes string pool");
                readPackage(position, next);
            }
            position = next;
        }
        if (strings == null) throw bad("No string pool");
    }
    private static IllegalArgumentException bad(String message) {
        return new IllegalArgumentException("Unsupported or invalid APK resources: "+message);
    }
    private void range(int offset, long length, int limit) {
        if (offset < 0 || length < 0 || offset > limit || length > limit-offset) throw bad("Out of bounds");
    }
    private int u8(int offset) { range(offset, 1, bytes.limit()); return bytes.get(offset)&255; }
    private int u16(int offset) { range(offset, 2, bytes.limit()); return bytes.getShort(offset)&65535; }
    private int i32(int offset) { range(offset, 4, bytes.limit()); return bytes.getInt(offset); }
    private int positive(int offset) {
        int value = i32(offset);
        if (value < 0) throw bad("Negative offset or count");
        return value;
    }
    private int chunkEnd(int start, int parentEnd) {
        range(start, 8, parentEnd);
        int header = u16(start+2), size = positive(start+4);
        if (header < 8 || size < header) throw bad("Chunk header");
        range(start, size, parentEnd);
        return start+size;
    }
    private int[] length(int position, boolean utf8, int end) {
        int unit = utf8 ? 1 : 2;
        range(position, unit, end);
        int first = utf8 ? u8(position) : u16(position);
        int mask = utf8 ? 128 : 32768;
        position += unit;
        if ((first&mask) == 0) return new int[] {first, position};
        range(position, unit, end);
        int second = utf8 ? u8(position) : u16(position);
        return new int[] {((first&(mask-1)) << (utf8 ? 8 : 16))|second, position+unit};
    }
    private String[] stringPool(int start, int end) throws CharacterCodingException {
        if (u16(start) != 1 || u16(start+2) < 28) throw bad("String pool header");
        int count = positive(start+8), styles = positive(start+12), flags = i32(start+16);
        int relative = positive(start+20);
        if (count > 65536 || styles != 0) throw bad("Styled or oversized string pool");
        int header = u16(start+2);
        range(start+header, (long)count*4, end);
        if (relative < header+(long)count*4) throw bad("String data overlaps index");
        range(start, relative, end);
        String[] result = new String[count];
        boolean utf8 = (flags&256) != 0;
        for (int index = 0; index < count; index++) {
            int offset = positive(start+header+4*index);
            long absolute = (long)start+relative+offset;
            if (absolute > end) throw bad("String offset");
            int[] logical = length((int)absolute, utf8, end);
            int[] encoded = utf8 ? length(logical[1], true, end) : logical;
            int byteCount = utf8 ? encoded[0] : encoded[0]*2;
            if (encoded[0] > 65536 || logical[0] > 65536) throw bad("String length");
            range(encoded[1], (long)byteCount+(utf8 ? 1 : 2), end);
            int terminator = utf8 ? u8(encoded[1]+byteCount) : u16(encoded[1]+byteCount);
            if (terminator != 0) throw bad("String terminator");
            ByteBuffer slice = bytes.duplicate();
            slice.position(encoded[1]); slice.limit(encoded[1]+byteCount);
            result[index] = (utf8 ? StandardCharsets.UTF_8 : StandardCharsets.UTF_16LE)
                .newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT).decode(slice).toString();
            if (result[index].length() != logical[0]) throw bad("UTF-16 length mismatch");
        }
        return result;
    }
    private void readPackage(int start, int end) throws Exception {
        int header = u16(start+2);
        if (header < 284) throw bad("Package header");
        int packageId = positive(start+8);
        if (packageId < 1 || packageId > 255 || (header >= 288 && i32(start+284) != 0))
            throw bad("Dynamic package or type offset");
        int relative = positive(start+268);
        range(start, relative, end);
        int typePool = start+relative;
        String[] types = stringPool(typePool, chunkEnd(typePool, end));
        for (int position = start+header; position < end;) {
            int next = chunkEnd(position, end);
            if (u16(position) == 0x201) readType(position, next, packageId, types);
            position = next;
        }
    }
    private void readType(int start, int end, int packageId, String[] types) {
        int header = u16(start+2);
        if (header < 24) throw bad("Type header");
        int type = u8(start+8);
        if (type == 0 || type > types.length) throw bad("Type index");
        if (!types[type-1].equals("string")) return;
        if (u8(start+9) != 0) throw bad("Sparse or compact string type");
        int configSize = positive(start+20);
        if (configSize < 4 || configSize > header-20) throw bad("Configuration size");
        for (int offset = start+24; offset < start+20+configSize; offset++) {
            if (u8(offset) != 0) return; // Only the default configuration is selected.
        }
        int count = positive(start+12), relative = positive(start+16);
        if (count > 65536 || relative < header+(long)count*4) throw bad("Entry count or start");
        range(start+header, (long)count*4, end);
        range(start, relative, end);
        for (int index = 0; index < count; index++) {
            int offset = i32(start+header+index*4);
            if (offset == -1) continue;
            long absolute = (long)start+relative+offset;
            if (offset < 0 || absolute > end) throw bad("Entry offset");
            int entry = (int)absolute;
            range(entry, 8, end);
            int size = u16(entry);
            if (size < 8 || (u16(entry+2)&~6) != 0) throw bad("Complex string entry");
            range(entry, (long)size+8, end);
            int value = entry+size;
            if (u16(value) != 8 || u8(value+2) != 0) throw bad("Value header");
            int kind = u8(value+3), data = i32(value+4);
            if (kind != 1 && kind != 3) throw bad("Non-string value");
            int id = (packageId<<24)|(type<<16)|index;
            if (values.put(id, new int[] {kind, data}) != null) throw bad("Duplicate default entry");
        }
    }
    public String getString(int resourceId) {
        for (int depth = 0; depth < 16; depth++) {
            int[] value = values.get(resourceId);
            if (value == null) throw bad("String not found: "+Integer.toHexString(resourceId));
            if (value[0] == 3) {
                if (value[1] < 0 || value[1] >= strings.length) throw bad("String index");
                return strings[value[1]];
            }
            resourceId = value[1];
        }
        throw bad("Cyclic or deep resource reference");
    }
}
