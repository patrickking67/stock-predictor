// Draws the simulated-price demo. All numbers come from fit.js; nothing is fetched.
import { FORECAST_DAYS, backtest, project, randomWalk } from "./fit.js";

const SVG_NS = "http://www.w3.org/2000/svg";
const W = 640;
const H = 280;
const PAD = { left: 52, right: 12, top: 12, bottom: 24 };
const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

const chart = document.getElementById("chart");
const caption = document.getElementById("chart-caption");
const facts = document.getElementById("facts");
const backtestText = document.getElementById("backtest-text");
const seedInput = document.getElementById("seed");

function el(name, attrs) {
    const node = document.createElementNS(SVG_NS, name);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    return node;
}

function path(points) {
    return "M" + points.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join("L");
}

function draw(seed) {
    const prices = randomWalk(seed);
    const fit = project(prices, FORECAST_DAYS);
    const total = prices.length + FORECAST_DAYS;
    const all = [...prices, ...fit.trend, ...fit.future];
    const lo = Math.min(...all);
    const hi = Math.max(...all);
    const span = hi - lo || 1;
    const x = (i) => PAD.left + (i / (total - 1)) * (W - PAD.left - PAD.right);
    const y = (v) => H - PAD.bottom - ((v - lo) / span) * (H - PAD.top - PAD.bottom);

    chart.replaceChildren();
    chart.append(
        el("rect", {
            class: "zone",
            x: x(prices.length - 1),
            y: PAD.top,
            width: x(total - 1) - x(prices.length - 1),
            height: H - PAD.top - PAD.bottom,
        }),
    );
    for (let k = 0; k <= 4; k++) {
        const value = lo + (span * k) / 4;
        chart.append(el("line", { class: "grid", x1: PAD.left, x2: W - PAD.right, y1: y(value), y2: y(value) }));
        const label = el("text", { class: "tick", x: PAD.left - 6, y: y(value) + 4, "text-anchor": "end" });
        label.textContent = "$" + Math.round(value);
        chart.append(label);
    }
    chart.append(el("path", { class: "price", d: path(prices.map((v, i) => [x(i), y(v)])) }));
    const line = fit.trend.map((v, i) => [x(i), y(v)]);
    chart.append(el("path", { class: "fit", d: path(line) }));
    const tail = [[x(prices.length - 1), y(fit.trend[prices.length - 1])], ...fit.future.map((v, i) => [x(prices.length + i), y(v)])];
    chart.append(el("path", { class: "fit future", d: path(tail) }));

    const end = fit.future[fit.future.length - 1];
    caption.textContent =
        `Simulation ${seed}: 252 simulated daily closes in blue, the fitted straight line in red, continued ${FORECAST_DAYS} days into the shaded area where it ends at ${money.format(end)}.`;

    const rows = [
        ["Last simulated price", money.format(prices[prices.length - 1])],
        ["Slope of the line", `${fit.slope < 0 ? "-" : "+"}${money.format(Math.abs(fit.slope))} per day`],
        ["R squared (in sample)", fit.r2.toFixed(2)],
    ];
    facts.replaceChildren();
    for (const [term, value] of rows) {
        const box = document.createElement("div");
        const dt = document.createElement("dt");
        const dd = document.createElement("dd");
        dt.textContent = term;
        dd.textContent = value;
        box.append(dt, dd);
        facts.append(box);
    }

    const test = backtest(prices);
    backtestText.textContent = test
        ? `Walk-forward test on these prices: over ${test.windows} windows of ${test.horizonDays} days the line missed by ${money.format(test.lineMae)} on average and "the price stays put" missed by ${money.format(test.naiveMae)}. The line was closer in ${test.lineBeatNaivePct.toFixed(1)}% of windows. These prices have no trend, so a straight line has nothing real to find.`
        : "";
}

function run() {
    const seed = Math.min(999999, Math.max(1, Math.trunc(Number(seedInput.value)) || 1));
    seedInput.value = String(seed);
    draw(seed);
}

document.getElementById("demo-form").addEventListener("submit", (event) => {
    event.preventDefault();
    run();
});
document.getElementById("again").addEventListener("click", () => {
    seedInput.value = String(1 + Math.floor(Math.random() * 999999));
    run();
});
run();
