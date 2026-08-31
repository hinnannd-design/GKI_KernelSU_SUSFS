#!/usr/bin/env python3
"""Scan kernel tree for `source "..."` Kconfig references whose target file is
missing (MiCode ships an incomplete source: hwid/, mca/, etc.) and create empty
stub Kconfig files so kconfig parsing can proceed. Also stub empty Makefiles."""
import os
import re
import sys

root = sys.argv[1] if len(sys.argv) > 1 else 'kernel'
created = []

for dirpath, dirnames, filenames in os.walk(root):
    if 'Kconfig' not in filenames:
        continue
    kpath = os.path.join(dirpath, 'Kconfig')
    try:
        txt = open(kpath, encoding='utf-8', errors='ignore').read()
    except OSError:
        continue
    for m in re.finditer(r'source\s+"([^"]+)"', txt):
        ref = m.group(1)
        candidates = [
            os.path.normpath(os.path.join(root, ref)),
            os.path.normpath(os.path.join(dirpath, ref)),
        ]
        target = None
        for c in candidates:
            if os.path.exists(c):
                target = c
                break
        if target is None:
            # use first candidate (root-relative, standard convention)
            target = candidates[0]
            try:
                d = os.path.dirname(target)
                # lexists: also true for dangling symlinks
                if os.path.lexists(d) and not os.path.isdir(d):
                    if os.path.islink(d):
                        os.unlink(d)
                    else:
                        os.remove(d)
                if not os.path.isdir(d):
                    os.makedirs(d, exist_ok=True)
                open(target, 'w').close()
                created.append(target)
            except OSError as e:
                print('skip', target, ':', e)

# also stub missing Makefiles in dirs referenced by obj-$(CONFIG_*) += xxx/
for dirpath, dirnames, filenames in os.walk(root):
    if 'Makefile' not in filenames:
        continue
    mpath = os.path.join(dirpath, 'Makefile')
    try:
        txt = open(mpath, encoding='utf-8', errors='ignore').read()
    except OSError:
        continue
    for m in re.finditer(r'obj-\$\(CONFIG_[^)]+\)\s*\+?=\s*([A-Za-z0-9_\-./]+)/', txt):
        sub = m.group(1)
        subdir = os.path.normpath(os.path.join(dirpath, sub))
        if os.path.isdir(subdir):
            if not os.path.exists(os.path.join(subdir, 'Makefile')):
                open(os.path.join(subdir, 'Makefile'), 'w').close()
                created.append(os.path.join(subdir, 'Makefile'))

print('created %d stub(s):' % len(created))
for c in created:
    print('  ', c)
