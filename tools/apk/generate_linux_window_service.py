#!/usr/bin/env python3
"""Generate the Linux boundary for all original IWindowManager methods, with explicit unsupported APIs."""
import argparse,hashlib,json,subprocess
from pathlib import Path
def parameters(text):
    result, start, depth = [], 0, 0
    for index, char in enumerate(text):
        if char == '<': depth += 1
        elif char == '>': depth -= 1
        elif char == ',' and depth == 0:
            result.append(text[start:index].strip()); start = index+1
    if text.strip(): result.append(text[start:].strip())
    return result

parser=argparse.ArgumentParser()
parser.add_argument('--bindings',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--check',action='store_true')
args=parser.parse_args()
proof=json.loads((args.bindings/'provenance.json').read_text())
jar=args.bindings/'bindings.jar'
assert hashlib.sha256(jar.read_bytes()).hexdigest()==proof['bindings_jar_sha256']
text=subprocess.check_output(['/usr/lib/jvm/java-17-openjdk/bin/javap','-classpath',str(jar),'-public','android.view.IWindowManager'],text=True)
lines=['package org.archtv.aosplinux;','',
 '// Generated from the complete original IWindowManager contract.',
 'public final class LinuxWindowService extends LocalServiceBinder implements android.view.IWindowManager {',
 '    private final WindowPolicyState policy;',
 '    public LinuxWindowService(java.nio.file.Path path) throws java.io.IOException {',
 '        super("android.view.IWindowManager");policy=new WindowPolicyState(path);', '    }',
 '    private WindowPolicyState.Snapshot state(int display) throws android.os.DeadObjectException {',
 '        if (!isBinderAlive()) throw new android.os.DeadObjectException();',
 '        if (display!=0) throw new IllegalArgumentException("Only the app virtual display 0 is supported");',
 '        try { return policy.read(); } catch (java.io.IOException failure) {',
 '            try { close(); } catch (RuntimeException callback) { failure.addSuppressed(callback); }',
 '            android.os.DeadObjectException dead=new android.os.DeadObjectException();dead.initCause(failure);throw dead;',
 '        }', '    }']
count=supported=0
for line in text.splitlines():
    line=line.strip().replace('$','.')
    if ' abstract ' not in line or not line.endswith(';'):continue
    declaration=line.split(' abstract ',1)[1][:-1]
    signature=declaration.split(' throws ',1)[0]
    throws=' throws '+declaration.split(' throws ',1)[1] if ' throws ' in declaration else ''
    head,tail=signature.split('(',1);result,name=head.rsplit(' ',1);types=parameters(tail[:-1])
    body=None
    if types==['int','android.graphics.Point'] and name in ('getInitialDisplaySize','getBaseDisplaySize'):
        initial=name=='getInitialDisplaySize'
        body='WindowPolicyState.Snapshot s=state(p0);java.util.Objects.requireNonNull(p1);p1.x=s.'+('initialWidth' if initial else 'width')+';p1.y=s.'+('initialHeight' if initial else 'height')+';'
    if types==['int']:
        body={'getInitialDisplayDensity':'return state(p0).density;', 'getBaseDisplayDensity':'return state(p0).density;',
              'hasNavigationBar':'return state(p0).navigationBar;'}.get(name,body)
    if not types:
        body={'useBLAST':'return state(0).blast;', 'getCurrentAnimatorScale':'return state(0).animatorScale;'}.get(name,body)
    if body is None:body='throw new UnsupportedOperationException("Unsupported Linux window API: '+name+'");'
    else:supported+=1
    lines+=['    @Override public '+result+' '+name+'('+', '.join(t+' p'+str(i) for i,t in enumerate(types))+')'+throws+' {', '        '+body, '    }'];count+=1
lines+=['}',''];output='\n'.join(lines)
assert count==proof['interface_methods_count'] and supported==7
if args.check:assert args.output.read_text()==output
else:
    with args.output.open('x') as stream:stream.write(output)
print(json.dumps({'contract_methods':count,'supported_methods':supported,'unsupported_methods':count-supported}))
