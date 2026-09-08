# Build status after folder organization

Source has been collected and Python workspace paths adjusted. Original working files are preserved in ../../archive. No images were rebuilt or written to USB during organization.

Current local entry points (run from KM6):

```
python3 source/firmware/build_modified.py
python3 source/usb/prepare.py
python3 source/usb/integrate.py
```

These are build commands, not a sequence to run blindly. The firmware builder expects archive/Stock and archive/output/analysis. USB preparation expects an extracted original image, upstream boot templates and local mcopy. Integration expects the prepared baseline image, original extracted rootfs, a built Maxio module and a complete staged module tree processed by depmod. It overwrites generated image files in archive/output.

Before a standalone build release: provide pinned dependency fetching, clean cross-compilation instructions for Maxio and kernel host tools, automatic input extraction/staging, and fresh-workspace verification. Current recipes depend on the archived build inputs. Driver source edits require rebuilding the module before integration; integration currently consumes the archived compiled module.

Archived reports and scripts may contain old absolute paths and superseded status statements. They are historical evidence, not the maintained source entry points. The original Project.md includes restrictions later superseded by explicit user authorization; it is retained as historical context only.
