// SPDX-License-Identifier: MIT
// Read-only validation and device-mapper table output for the tested KM6 layout.
#define _POSIX_C_SOURCE 200809L
#include <fcntl.h>
#include <inttypes.h>
#include <linux/fs.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <unistd.h>

#define MIB UINT64_C(1048576)
#define DISK_BYTES UINT64_C(62545461248)
static uint32_t le32(const unsigned char *p) {
    return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
static uint64_t le64(const unsigned char *p) { return le32(p) | (uint64_t)le32(p+4)<<32; }
static int fail(const char *message) { fprintf(stderr, "KM6 MPT: %s\n", message); return 1; }
int main(int argc, char **argv) {
    int backup = argc == 3 && !strcmp(argv[1], "--table-backup");
    if (argc != 1 && !backup) return fail("usage: mpt-map [--table-backup regular-file]");
    const char *path = backup ? argv[2] : "/dev/mmcblk1";
    int fd = open(path, O_RDONLY | O_CLOEXEC);
    if (fd < 0) return fail("cannot open input");
    struct stat st;
    uint64_t bytes = DISK_BYTES;
    if (fstat(fd, &st)) return fail("cannot stat input");
    if (backup ? !S_ISREG(st.st_mode) : (!S_ISBLK(st.st_mode) || ioctl(fd, BLKGETSIZE64, &bytes)))
        return fail("unexpected input type");
    if (bytes != DISK_BYTES) return fail("unexpected eMMC capacity");
    unsigned char table[1304];
    ssize_t n = pread(fd, table, sizeof table, backup ? 0 : 36*MIB);
    close(fd);
    if (n != sizeof table) return fail("short table read");
    if (memcmp(table, "MPT\00001.00.00\0\0\0", 16) || le32(table+16) != 20)
        return fail("expected the installed dual-boot MPT v1 table");
    uint32_t sum = 0;
    for (int i=0; i<10; i++) sum += le32(table+24+4*i);
    if (sum*20 != le32(table+20)) return fail("invalid v1 checksum");
    uint64_t end = 0, offsets[20], sizes[20];
    char names[20][17];
    for (int i=0; i<20; i++) {
        const unsigned char *p = table+24+40*i;
        memcpy(names[i], p, 16); names[i][16] = 0;
        if (!memchr(p, 0, 16) || !p[0] || le32(p+36)) return fail("invalid entry");
        for (int j=0; j<i; j++) if (!strcmp(names[i], names[j])) return fail("duplicate name");
        sizes[i] = le64(p+16); offsets[i] = le64(p+24);
        if (!sizes[i] || sizes[i]%512 || offsets[i]%512 || offsets[i]<end ||
            offsets[i]>bytes || sizes[i]>bytes-offsets[i]) return fail("invalid partition bounds");
        end = offsets[i]+sizes[i];
    }
    if (strcmp(names[17], "data") || offsets[17]!=2786*MIB || sizes[17]!=32768*MIB ||
        strcmp(names[18], "linuxboot") || offsets[18]!=35562*MIB || sizes[18]!=256*MIB ||
        strcmp(names[19], "linuxroot") || offsets[19]!=35826*MIB || end!=bytes)
        return fail("layout does not match this installer");
    for (int i=18; i<20; i++)
        printf("km6-%s 0 %" PRIu64 " linear /dev/mmcblk1 %" PRIu64 "\n", names[i], sizes[i]/512, offsets[i]/512);
    return 0;
}
