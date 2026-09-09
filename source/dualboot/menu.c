// SPDX-License-Identifier: MIT
// KM6 early-boot chooser. Returns 0 for Android, 10 for Debian; never boots or writes storage.
#define _POSIX_C_SOURCE 200809L
#include <errno.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>

static struct termios saved;
static int have_term;
static volatile sig_atomic_t stopped;
static double now(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec / 1e9;
}
static void restore(void) {
    if (have_term) tcsetattr(STDIN_FILENO, TCSANOW, &saved);
    fputs("\033[0m\033[?25h\033[2J\033[H", stdout);
    fflush(stdout);
}
static void stop(int sig) { stopped = sig; }
static void line(int row, int col, const char *text) {
    printf("\033[%d;%dH%s", row, col, text);
}
int main(int argc, char **argv) {
    int delay = 8, selected = 0, paused = 0, escape = 0;
    if (argc == 3 && !strcmp(argv[1], "--timeout")) {
        char *end;
        long n = strtol(argv[2], &end, 10);
        if (!*argv[2] || *end || n < 0 || n > 300) return 2;
        delay = (int)n;
    } else if (argc != 1) {
        fputs("Usage: km6-menu [--timeout 0..300]\n", stderr);
        return 2;
    }
    if (!isatty(STDIN_FILENO) || tcgetattr(STDIN_FILENO, &saved)) return 2;
    struct termios raw = saved;
    raw.c_lflag &= ~(ICANON | ECHO);
    raw.c_cc[VMIN] = 0;
    raw.c_cc[VTIME] = 0;
    if (tcsetattr(STDIN_FILENO, TCSANOW, &raw)) return 2;
    have_term = 1;
    atexit(restore);
    signal(SIGTERM, stop);
    signal(SIGINT, stop);
    signal(SIGHUP, stop);
    double deadline = now() + delay;
    int last_seconds = -1, last_selected = -1, last_paused = -1;
    while (!stopped) {
        int seconds = (int)(deadline - now() + 0.999);
        if (!paused && seconds <= 0) return 0;
        if (seconds != last_seconds || selected != last_selected || paused != last_paused) {
            struct winsize ws = {0};
            ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws);
            int col = ws.ws_col > 60 ? (ws.ws_col - 60) / 2 : 1;
            int row = ws.ws_row > 14 ? (ws.ws_row - 14) / 2 : 1;
            fputs("\033[?25l\033[0;37;40m\033[2J", stdout);
            line(row, col, "KM6 DELUXE");
            line(row + 2, col, "Choose an operating system");
            line(row + 5, col, selected == 0 ? "\033[1;37;44m  > 1. Android TV (default)              \033[0;37;40m" : "    1. Android TV (default)");
            line(row + 7, col, selected == 1 ? "\033[1;37;44m  > 2. Debian Linux                     \033[0;37;40m" : "    2. Debian Linux");
            line(row + 10, col, "Up/Down or 1/2 to select. Enter to boot.");
            if (paused) line(row + 12, col, "Automatic boot paused. Press Enter to continue.");
            else {
                char text[80];
                snprintf(text, sizeof text, "Android TV starts automatically in %d seconds.", seconds);
                line(row + 12, col, text);
            }
            fflush(stdout);
            last_seconds = seconds; last_selected = selected; last_paused = paused;
        }
        struct pollfd pfd = {STDIN_FILENO, POLLIN, 0};
        int ready = poll(&pfd, 1, 100);
        if (ready < 0) { if (errno == EINTR) continue; return 2; }
        if (pfd.revents & (POLLHUP | POLLERR | POLLNVAL)) return 2;
        if (!(pfd.revents & POLLIN)) continue;
        unsigned char buf[32];
        ssize_t n = read(STDIN_FILENO, buf, sizeof buf);
        for (ssize_t i = 0; i < n; i++) {
            unsigned char ch = buf[i];
            if (escape == 1) { escape = ch == '[' || ch == 'O' ? 2 : 0; continue; }
            if (escape == 2) {
                if (ch == 'A') { selected = 0; paused = 1; }
                if (ch == 'B') { selected = 1; paused = 1; }
                escape = 0; continue;
            }
            if (ch == 27) { escape = 1; continue; }
            if (ch == '1') { selected = 0; paused = 1; }
            if (ch == '2') { selected = 1; paused = 1; }
            if (ch == '\n' || ch == '\r') return selected ? 10 : 0;
        }
    }
    return 2;
}
