// The same straight-line model and walk-forward backtest as main.py, in plain JS.
// No network, no dependencies. The demo page feeds it simulated prices only.

export const FORECAST_DAYS = 5;
export const MIN_HISTORY_POINTS = 20;
export const BACKTEST_STRIDE = 5;

/** Small seeded random generator (mulberry32). Same seed, same numbers. */
export function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
        a = (a + 0x6d2b79f5) >>> 0;
        let t = a;
        t = Math.imul(t ^ (t >>> 15), t | 1);
        t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
}

/** A made-up price series: a random walk with no trend built in. */
export function randomWalk(seed, points = 252, start = 100, step = 1.2) {
    const rand = mulberry32(seed);
    const out = [start];
    for (let i = 1; i < points; i++) {
        const move = (rand() + rand() + rand() - 1.5) * step * 2;
        out.push(Math.max(1, out[i - 1] + move));
    }
    return out;
}

/** Ordinary least squares of y on 0..n-1. */
export function fitLine(ys) {
    const n = ys.length;
    if (n < 2) throw new Error("need at least 2 points");
    const meanX = (n - 1) / 2;
    const meanY = ys.reduce((s, v) => s + v, 0) / n;
    let sxy = 0;
    let sxx = 0;
    let syy = 0;
    for (let i = 0; i < n; i++) {
        sxy += (i - meanX) * (ys[i] - meanY);
        sxx += (i - meanX) ** 2;
        syy += (ys[i] - meanY) ** 2;
    }
    const slope = sxy / sxx;
    const intercept = meanY - slope * meanX;
    const r2 = syy === 0 ? 1 : (sxy * sxy) / (sxx * syy);
    return { slope, intercept, r2 };
}

/** Fit the line and extend it `days` steps. */
export function project(ys, days = FORECAST_DAYS) {
    if (days < 1) throw new Error("days must be at least 1");
    if (ys.length < MIN_HISTORY_POINTS) throw new Error("not enough history");
    const { slope, intercept, r2 } = fitLine(ys);
    const trend = ys.map((_, i) => intercept + slope * i);
    const future = Array.from({ length: days }, (_, k) => intercept + slope * (ys.length + k));
    return { slope, intercept, r2, trend, future };
}

/** Walk-forward test: the line versus "the price stays at the last close". */
export function backtest(ys, days = FORECAST_DAYS, minTrain = MIN_HISTORY_POINTS, stride = BACKTEST_STRIDE) {
    if (days < 1 || stride < 1) throw new Error("days and stride must be at least 1");
    const lineErrors = [];
    const naiveErrors = [];
    for (let origin = minTrain; origin <= ys.length - days; origin += stride) {
        const { slope, intercept } = fitLine(ys.slice(0, origin));
        const last = ys[origin - 1];
        let lineSum = 0;
        let naiveSum = 0;
        for (let k = 0; k < days; k++) {
            const actual = ys[origin + k];
            lineSum += Math.abs(intercept + slope * (origin + k) - actual);
            naiveSum += Math.abs(last - actual);
        }
        lineErrors.push(lineSum / days);
        naiveErrors.push(naiveSum / days);
    }
    if (lineErrors.length === 0) return null;
    const mean = (a) => a.reduce((s, v) => s + v, 0) / a.length;
    const wins = lineErrors.filter((v, i) => v < naiveErrors[i]).length;
    return {
        windows: lineErrors.length,
        horizonDays: days,
        lineMae: mean(lineErrors),
        naiveMae: mean(naiveErrors),
        lineBeatNaivePct: (wins / lineErrors.length) * 100,
    };
}
