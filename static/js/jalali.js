/**
 * توابع تبدیل جلالی ↔ میلادی.
 *
 * ─── مبنا: ───
 * الگوریتم jalaali-js (Behrang Noruzi Niya)
 * https://github.com/jalaali/jalaali-js
 *
 * ─── استفاده: ───
 *   Jalali.toJalali(2024, 9, 26)      → { jy: 1403, jm: 7, jd: 5 }
 *   Jalali.toGregorian(1403, 7, 5)    → { gy: 2024, gm: 9, gd: 26 }
 *   Jalali.isLeapJalaliYear(1403)     → true/false
 */

(function (global) {
    'use strict';

    // ═══════════════════════════════════════════════════════════
    //  Helpers
    // ═══════════════════════════════════════════════════════════

    var breaks = [
        -61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210,
        1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178
    ];

    function div(a, b) {
        return ~~(a / b);
    }

    function mod(a, b) {
        return a - ~~(a / b) * b;
    }

    // ═══════════════════════════════════════════════════════════
    //  Jalali → Gregorian
    // ═══════════════════════════════════════════════════════════

    function jalCal(jy, withoutLeap) {
        var bl = breaks.length;
        var gy = jy + 621;
        var leapJ = -14;
        var jp = breaks[0];
        var jm, jump, leap, leapG, march, n, i;

        if (jy < jp || jy >= breaks[bl - 1]) {
            throw new Error('Invalid Jalaali year ' + jy);
        }

        for (i = 1; i < bl; i += 1) {
            jm = breaks[i];
            jump = jm - jp;
            if (jy < jm) break;
            leapJ = leapJ + div(jump, 33) * 8 + div(mod(jump, 33), 4);
            jp = jm;
        }
        n = jy - jp;

        leapJ = leapJ + div(n, 33) * 8 + div(mod(n, 33) + 3, 4);
        if (mod(jump, 33) === 4 && jump - n === 4) {
            leapJ += 1;
        }

        leapG = div(gy, 4) - div((div(gy, 100) + 1) * 3, 4) - 150;
        march = 20 + leapJ - leapG;

        if (!withoutLeap) {
            if (jump - n < 6) {
                n = n - jump + div(jump + 4, 33) * 33;
            }
            leap = mod(mod(n + 1, 33) - 1, 4);
            if (leap === -1) {
                leap = 4;
            }
        }

        return {
            leap: leap,
            gy: gy,
            march: march
        };
    }

    function j2d(jy, jm, jd) {
        var r = jalCal(jy, true);
        return g2d(r.gy, 3, r.march) + (jm - 1) * 31 - div(jm, 7) * (jm - 7) + jd - 1;
    }

    function d2j(jdn) {
        var gy = d2g(jdn).gy;
        var jy = gy - 621;
        var r = jalCal(jy, false);
        var jdn1f = g2d(gy, 3, r.march);
        var jd, jm, k;

        k = jdn - jdn1f;
        if (k >= 0) {
            if (k <= 185) {
                jm = 1 + div(k, 31);
                jd = mod(k, 31) + 1;
                return { jy: jy, jm: jm, jd: jd };
            } else {
                k -= 186;
            }
        } else {
            jy -= 1;
            k += 179;
            if (r.leap === 1) {
                k += 1;
            }
        }
        jm = 7 + div(k, 30);
        jd = mod(k, 30) + 1;
        return { jy: jy, jm: jm, jd: jd };
    }

    // ═══════════════════════════════════════════════════════════
    //  Gregorian helpers
    // ═══════════════════════════════════════════════════════════

    function g2d(gy, gm, gd) {
        var d = div((gy + div(gm - 8, 6) + 100100) * 1461, 4)
            + div(153 * mod(gm + 9, 12) + 2, 5)
            + gd - 34840408;
        d = d - div(div(gy + 100100 + div(gm - 8, 6), 100) * 3, 4) + 752;
        return d;
    }

    function d2g(jdn) {
        var j, i, gd, gm, gy;
        j = 4 * jdn + 139361631;
        j = j + div(div(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908;
        i = div(mod(j, 1461), 4) * 5 + 308;
        gd = div(mod(i, 153), 5) + 1;
        gm = mod(div(i, 153), 12) + 1;
        gy = div(j, 1461) - 100100 + div(8 - gm, 6);
        return { gy: gy, gm: gm, gd: gd };
    }

    // ═══════════════════════════════════════════════════════════
    //  Public API
    // ═══════════════════════════════════════════════════════════

    function toJalali(gy, gm, gd) {
        var result = d2j(g2d(gy, gm, gd));
        return { jy: result.jy, jm: result.jm, jd: result.jd };
    }

    function toGregorian(jy, jm, jd) {
        var result = d2g(j2d(jy, jm, jd));
        return { gy: result.gy, gm: result.gm, gd: result.gd };
    }

    function isLeapJalaliYear(jy) {
        return jalCal(jy, false).leap === 0;
    }

    function jalaliMonthLength(jy, jm) {
        if (jm <= 6) return 31;
        if (jm <= 11) return 30;
        if (isLeapJalaliYear(jy)) return 30;
        return 29;
    }

    var Jalali = {
        toJalali: toJalali,
        toGregorian: toGregorian,
        isLeapJalaliYear: isLeapJalaliYear,
        jalaliMonthLength: jalaliMonthLength,
    };

    // ─── UMD export ───
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = Jalali;
    } else {
        global.Jalali = Jalali;
    }
})(typeof window !== 'undefined' ? window : this);