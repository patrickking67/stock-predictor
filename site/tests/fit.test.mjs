import assert from "node:assert/strict";
import { test } from "node:test";
import { backtest, fitLine, mulberry32, project, randomWalk } from "../fit.js";

// Same series and expected values as the Python tests in tests/test_prediction.py.
const sample = Array.from({ length: 60 }, (_, i) => 100 + ((i * 7919) % 13) + i * 0.3);

test("a straight line is extended exactly", () => {
    const ys = Array.from({ length: 30 }, (_, i) => 10 + i);
    const result = project(ys, 5);
    assert.deepEqual(result.future.map((v) => Math.round(v)), [40, 41, 42, 43, 44]);
    assert.ok(Math.abs(result.slope - 1) < 1e-9);
    assert.ok(Math.abs(result.r2 - 1) < 1e-9);
});

test("matches the Python model on a shared series", () => {
    const result = project(sample, 5);
    assert.deepEqual(result.future.map((v) => Number(v.toFixed(2))), [124.38, 124.69, 125.01, 125.32, 125.64]);
    assert.equal(Number(result.slope.toFixed(4)), 0.3151);
    assert.equal(Number(result.r2.toFixed(4)), 0.675);
});

test("backtest matches the Python backtest on a shared series", () => {
    const result = backtest(sample, 5);
    assert.equal(result.windows, 8);
    assert.equal(Number(result.lineMae.toFixed(4)), 3.5486);
    assert.equal(Number(result.naiveMae.toFixed(4)), 4.89);
    assert.equal(result.lineBeatNaivePct, 75);
});

test("backtest is null when history is too short", () => {
    assert.equal(backtest(new Array(22).fill(1), 5), null);
});

test("flat prices tie the naive guess and do not count as a win", () => {
    const result = backtest(new Array(60).fill(50), 5);
    assert.equal(result.lineBeatNaivePct, 0);
});

test("bad arguments are rejected", () => {
    assert.throws(() => project(sample, 0));
    assert.throws(() => project([1, 2, 3], 5));
    assert.throws(() => fitLine([1]));
    assert.throws(() => backtest(sample, 5, 20, 0));
});

test("the same seed gives the same simulated prices", () => {
    assert.deepEqual(randomWalk(7, 50), randomWalk(7, 50));
    assert.notDeepEqual(randomWalk(7, 50), randomWalk(8, 50));
    assert.equal(randomWalk(1).length, 252);
    assert.ok(mulberry32(1)() < 1);
});
