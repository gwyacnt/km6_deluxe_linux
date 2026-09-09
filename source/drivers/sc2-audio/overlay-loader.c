// SPDX-License-Identifier: GPL-2.0
/* Experimental live overlays, limited to the SC2 test board. No boot changes.
 * No unload entry: clock providers contain static registration data and are
 * intentionally retained until reboot rather than removed/reprobed in place.
 */
#include <linux/module.h>
#include <linux/firmware.h>
#include <linux/device.h>
#include <linux/of.h>
static char *overlay = "km6-audio-clock.dtbo";
module_param(overlay, charp, 0400);
static int __init km6_overlay_init(void)
{
    const struct firmware *fw;
    struct device *dev;
    int ret, id;
    if (!of_machine_is_compatible("amlogic,sc2"))
        return -ENODEV;
    dev = root_device_register(KBUILD_MODNAME);
    if (IS_ERR(dev))
        return PTR_ERR(dev);
    ret = request_firmware(&fw, overlay, dev);
    if (!ret) {
        ret = of_overlay_fdt_apply(fw->data, fw->size, &id, NULL);
        release_firmware(fw);
        if (!ret)
            pr_info("KM6 audio experiment: applied %s overlay id %d; reboot to remove\n", overlay, id);
    }
    root_device_unregister(dev);
    return ret;
}
module_init(km6_overlay_init);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("KM6 SC2 experimental live audio overlay loader");
