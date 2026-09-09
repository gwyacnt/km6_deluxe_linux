// SPDX-License-Identifier: GPL-2.0
/* Read-only SC2 audio clock/register inspection. Never writes registers. */
#include <linux/module.h>
#include <linux/io.h>
#include <linux/clk.h>
#include <linux/of.h>
#include <linux/of_clk.h>
#include <linux/of_platform.h>
#include <sound/soc.h>
static void __iomem *audio;
static int report_get(char *buf, const struct kernel_param *kp)
{
    static const u32 regs[] = {0,4,0x10,0x28,0x2c,0x30,0x34,0x50,0x54,0x98,
        0x1c0,0x1c4,0x1c8,0x1cc,0x1d0,0x1d4,0x1d8,0x1e4,0x1e8,
        0x280,0x580,0x584,0x588,0x58c,0x590,0x594,0x598,0x59c,0x744};
    static const u32 ids[] = {29,37,38,51,61,81,88,122,129,136};
    struct of_phandle_args args = { .args_count = 1 };
    struct clk *clk;
    int n = 0, i;
    for (i = 0; i < ARRAY_SIZE(regs); i++)
        n += scnprintf(buf+n, PAGE_SIZE-n, "%03x: %08x\n", regs[i], readl(audio+regs[i]));
    args.np = of_find_node_by_path("/soc/bus@fe000000/clock-controller@330000");
    if (!args.np)
        return n;
    for (i = 0; i < ARRAY_SIZE(ids); i++) {
        args.args[0] = ids[i];
        clk = of_clk_get_from_provider(&args);
        if (IS_ERR(clk)) {
            n += scnprintf(buf+n, PAGE_SIZE-n, "clock %u error %ld\n", ids[i], PTR_ERR(clk));
        } else {
            n += scnprintf(buf+n, PAGE_SIZE-n, "clock %u rate %lu\n", ids[i], clk_get_rate(clk));
            clk_put(clk);
        }
    }
    of_node_put(args.np);
    return n;
}
static const struct kernel_param_ops report_ops = { .get = report_get };
module_param_cb(report, &report_ops, NULL, 0444);
static int dapm_get(char *buf, const struct kernel_param *kp)
{
    struct device_node *np = of_find_node_by_path("/audio-controller-km6");
    struct platform_device *pdev;
    struct snd_soc_component *component;
    struct snd_soc_dapm_widget *widget;
    struct snd_soc_dapm_path *path;
    struct snd_soc_card *card;
    int n = 0;
    if (!np) return -ENODEV;
    pdev = of_find_device_by_node(np);
    of_node_put(np);
    if (!pdev) return -ENODEV;
    component = snd_soc_lookup_component(&pdev->dev, NULL);
    if (!component || !component->card) { put_device(&pdev->dev); return -ENODEV; }
    card = component->card;
    snd_soc_dapm_mutex_lock(card);
    list_for_each_entry(widget, &card->widgets, list)
        n += scnprintf(buf+n, PAGE_SIZE-n, "W %s p=%u a=%u c=%u ep=%u\n",
             widget->name, widget->power, widget->active, widget->connected, widget->is_ep);
    list_for_each_entry(path, &card->paths, list)
        n += scnprintf(buf+n, PAGE_SIZE-n, "P %s <- %s c=%u\n",
             path->sink->name, path->source->name, path->connect);
    snd_soc_dapm_mutex_unlock(card);
    put_device(&pdev->dev);
    return n;
}
static const struct kernel_param_ops dapm_ops = { .get = dapm_get };
module_param_cb(dapm, &dapm_ops, NULL, 0444);
static int __init diag_init(void)
{
    if (!of_machine_is_compatible("amlogic,sc2"))
        return -ENODEV;
    audio = ioremap(0xfe330000, 0x1000);
    return audio ? 0 : -ENOMEM;
}
static void __exit diag_exit(void) { iounmap(audio); }
module_init(diag_init);
module_exit(diag_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Read-only KM6 audio register diagnostics");
