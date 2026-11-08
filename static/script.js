// Stock Predictor front end. Talks only to this app's own routes.
(function () {
    "use strict";

    var form = document.getElementById("predict-form");
    var input = document.getElementById("symbol");
    var submit = document.getElementById("submit");
    var statusEl = document.getElementById("status");
    var suggestions = document.getElementById("symbol-suggestions");
    var chart = null;
    var searchEnabled = true;
    var searchTimer = null;
    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    var money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

    function setStatus(message, isError) {
        statusEl.textContent = message;
        statusEl.classList.toggle("is-error", Boolean(isError));
        if (isError) {
            statusEl.setAttribute("role", "alert");
        } else {
            statusEl.setAttribute("role", "status");
        }
    }

    function setBusy(busy) {
        submit.disabled = busy;
        submit.textContent = busy ? "Fitting..." : "Fit the line";
    }

    function signed(value) {
        var text = money.format(Math.abs(value));
        return (value < 0 ? "-" : "+") + text;
    }

    function predict(symbol) {
        setBusy(true);
        setStatus("Fetching a year of prices for " + symbol + "...");
        fetch("/predict_stock?symbol=" + encodeURIComponent(symbol))
            .then(function (response) {
                return response.json().catch(function () {
                    throw new Error("The server sent an unreadable response. Try again.");
                });
            })
            .then(function (data) {
                if (data.error) {
                    throw new Error(data.error);
                }
                render(data);
                setStatus("Fitted a line through " + data.model.points + " daily closes for " + data.symbol + ".");
            })
            .catch(function (error) {
                var message = error instanceof TypeError ? "Could not reach the server. Check your connection." : error.message;
                setStatus(message, true);
            })
            .finally(function () {
                setBusy(false);
            });
    }

    function render(data) {
        var name = data.company_name ? data.company_name + " (" + data.symbol + ")" : data.symbol;
        document.getElementById("result-title").textContent = name;

        document.getElementById("latest-price").textContent = money.format(data.latest.price);
        document.getElementById("latest-meta").textContent =
            data.latest.source + (data.latest.as_of ? ", " + data.latest.as_of : "");
        document.getElementById("slope").textContent = signed(data.model.slope_per_day);
        document.getElementById("r-squared").textContent = data.model.r_squared.toFixed(2);

        var rows = document.getElementById("projection-rows");
        rows.replaceChildren();
        data.predictions.forEach(function (price, i) {
            var tr = document.createElement("tr");
            var day = document.createElement("td");
            var value = document.createElement("td");
            day.textContent = "+" + (i + 1);
            value.textContent = money.format(price);
            tr.append(day, value);
            rows.append(tr);
        });

        var notices = document.getElementById("notices");
        notices.replaceChildren();
        (data.notices || []).forEach(function (text) {
            var li = document.createElement("li");
            li.textContent = text;
            notices.append(li);
        });

        var first = data.history[0];
        var last = data.history[data.history.length - 1];
        var caption = document.getElementById("chart-caption");
        caption.textContent =
            "Blue: daily closes for " + data.symbol + " from " + first.date + " to " + last.date +
            ". Red: the straight line fitted to them, continued " + data.predictions.length +
            " trading days into the shaded area, where it ends at " +
            money.format(data.predictions[data.predictions.length - 1]) + ".";
        caption.hidden = false;

        document.getElementById("chart-empty").hidden = true;
        document.getElementById("chart-wrap").hidden = false;
        document.getElementById("result-body").hidden = false;
        drawChart(data, caption.textContent);
    }

    // Shades the projected days so the extended line reads as "beyond the data".
    var futureZone = {
        id: "futureZone",
        beforeDatasetsDraw: function (c, args, options) {
            var x = c.scales.x;
            var area = c.chartArea;
            var start = x.getPixelForValue(options.from);
            c.ctx.save();
            c.ctx.fillStyle = "rgba(180, 35, 44, 0.07)";
            c.ctx.fillRect(start, area.top, area.right - start, area.bottom - area.top);
            c.ctx.restore();
        }
    };

    function drawChart(data, label) {
        if (typeof Chart === "undefined") {
            setStatus("The chart library did not load, but the numbers below are still correct.", true);
            return;
        }
        var labels = data.history.map(function (p) { return p.date; });
        var closes = data.history.map(function (p) { return p.close; });
        var line = data.trend.slice();
        data.predictions.forEach(function (price, i) {
            labels.push("+" + (i + 1) + " day" + (i ? "s" : ""));
            closes.push(null);
            line.push(price);
        });

        var canvas = document.getElementById("stockChart");
        canvas.setAttribute("aria-label", label);
        if (chart) {
            chart.destroy();
        }
        chart = new Chart(canvas, {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Daily close",
                        data: closes,
                        borderColor: "#004d99",
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0
                    },
                    {
                        label: "Straight line",
                        data: line,
                        borderColor: "#b4232c",
                        borderWidth: 2,
                        pointRadius: 0,
                        segment: {
                            borderDash: function (ctx) {
                                return ctx.p0DataIndex >= data.history.length - 1 ? [6, 4] : undefined;
                            }
                        }
                    }
                ]
            },
            options: {
                maintainAspectRatio: false,
                animation: reduceMotion ? false : { duration: 600 },
                interaction: { mode: "index", intersect: false },
                scales: {
                    x: { ticks: { maxTicksLimit: 6, color: "#4a5d78" }, grid: { display: false } },
                    y: {
                        ticks: {
                            color: "#4a5d78",
                            callback: function (value) { return money.format(value); }
                        },
                        grid: { color: "#dbe5f1" }
                    }
                },
                plugins: {
                    legend: { labels: { color: "#0e2440", boxHeight: 2 } },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                return ctx.parsed.y === null ? null : ctx.dataset.label + ": " + money.format(ctx.parsed.y);
                            }
                        }
                    },
                    futureZone: { from: data.history.length - 1 }
                }
            },
            plugins: [futureZone]
        });
    }

    function loadSuggestions(term) {
        if (!searchEnabled || term.length < 2) {
            return;
        }
        fetch("/symbol_search?q=" + encodeURIComponent(term))
            .then(function (response) {
                if (response.status === 503) {
                    searchEnabled = false; // No key on the server; stop asking.
                }
                return response.ok ? response.json() : { matches: [] };
            })
            .then(function (data) {
                suggestions.replaceChildren();
                data.matches.forEach(function (match) {
                    var option = document.createElement("option");
                    option.value = match.symbol;
                    option.label = match.name;
                    suggestions.append(option);
                });
            })
            .catch(function () {
                suggestions.replaceChildren();
            });
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        var symbol = input.value.split(" - ")[0].trim().toUpperCase();
        if (!symbol) {
            setStatus("Enter a ticker symbol, for example AAPL.", true);
            input.focus();
            return;
        }
        predict(symbol);
    });

    input.addEventListener("input", function () {
        clearTimeout(searchTimer);
        var term = input.value.trim();
        searchTimer = setTimeout(function () { loadSuggestions(term); }, 300);
    });

    document.querySelectorAll(".pick").forEach(function (button) {
        button.addEventListener("click", function () {
            input.value = button.dataset.symbol;
            predict(button.dataset.symbol);
        });
    });

    var initial = new URLSearchParams(window.location.search).get("symbol");
    if (initial) {
        input.value = initial;
        form.requestSubmit();
    }
})();
