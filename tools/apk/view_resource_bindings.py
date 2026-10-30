"""Generate the single resource binding needed by original StateSet from pinned XML."""
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET


def generate(sources, manifest, output):
    paths = manifest['view_resource_inputs']
    inputs = {}
    for name in paths:
        path = sources/name
        item = next(item for item in manifest['files'] if item['path'] == name)
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if len(data) != item['bytes'] or digest != item['sha256']:
            raise ValueError('Resource input checksum mismatch: '+name)
        inputs[name] = digest
    attrs = ET.parse(sources/'core/res/res/values/attrs.xml').getroot()
    declarations = attrs.findall("declare-styleable[@name='ViewDrawableStates']")
    if len(declarations) != 1:
        raise ValueError('Expected one original ViewDrawableStates declaration')
    names = [item.attrib['name'] for item in declarations[0].findall('attr')]
    if len(names) != 10 or len(set(names)) != 10:
        raise ValueError('Unexpected original state set')
    public = ET.parse(sources/'core/res/res/values/public-final.xml').getroot()
    ids = {item.attrib['name']:int(item.attrib['id'],16)
           for item in public.findall("public[@type='attr']")}
    values = sorted((ids[name],name) for name in names)
    if len({value for value,name in values}) != 10:
        raise ValueError('Duplicate state ID')
    # AAPT styleable arrays are sorted by resource ID. Only this recorded binding
    # is emitted; other system resource fields remain absent and must fail.
    source = output/'com/android/internal/R.java'
    source.parent.mkdir(parents=True,exist_ok=True)
    source.write_text('// Generated from pinned AOSP attrs.xml and public-final.xml.\n'
        'package com.android.internal;\npublic final class R {\n'
        '  public static final class styleable {\n'
        '    public static final int[] ViewDrawableStates = new int[] {\n'+
        ''.join('      0x%08x, // %s\n' % (value,name) for value,name in values)+
        '    };\n  }\n}\n')
    return source, {'inputs_sha256':inputs,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'states':[{'name':name,'id':value} for value,name in values],
        'scope':'Only generated R.styleable.ViewDrawableStates IDs; no system resource table, theme values or other R fields.'}
