const products = [
  { name: "Mobile App", adoption: 74, previousAdoption: 69, taskSuccess: 91, defects: 18, sla: 98.2, nps: 42, incidents: 2, owner: "Growth Product" },
  { name: "Customer Portal", adoption: 63, previousAdoption: 65, taskSuccess: 84, defects: 31, sla: 96.1, nps: 31, incidents: 5, owner: "Self Service" },
  { name: "Billing Console", adoption: 58, previousAdoption: 52, taskSuccess: 88, defects: 15, sla: 99.1, nps: 39, incidents: 1, owner: "Revenue Ops" },
  { name: "Support Hub", adoption: 47, previousAdoption: 43, taskSuccess: 79, defects: 27, sla: 94.4, nps: 24, incidents: 7, owner: "Service Ops" }
];

const workflows = [
  ["Collect", "Pull adoption, conversion, defect, SLA, and support signals from product analytics and operations tools."],
  ["Validate", "QA source freshness, missing values, metric definitions, and release-note impact before dashboards refresh."],
  ["Analyze", "Compare current performance against previous period and isolate product, channel, or journey drivers."],
  ["Report", "Publish stakeholder dashboard notes with decisions, owners, risks, and next actions."]
];

const productFilter = document.querySelector("#productFilter");
const periodFilter = document.querySelector("#periodFilter");
const formatPercent = (value) => `${value.toFixed(1)}%`;

products.forEach((product) => productFilter.append(new Option(product.name, product.name)));

function rows() {
  return products
    .filter((product) => productFilter.value === "all" || product.name === productFilter.value)
    .map((product) => {
      const adoption = periodFilter.value === "current" ? product.adoption : product.previousAdoption;
      return { ...product, adoption };
    });
}

function average(data, key) {
  return data.reduce((sum, row) => sum + row[key], 0) / Math.max(data.length, 1);
}

function health(product) {
  return Math.round(product.adoption * 0.28 + product.taskSuccess * 0.34 + product.sla * 0.24 + Math.max(0, 100 - product.defects) * 0.14);
}

function statusFor(product) {
  if (product.incidents >= 6 || product.sla < 95) return ["Critical", "critical"];
  if (product.defects >= 25 || product.taskSuccess < 85) return ["Watch", "watch"];
  return ["Healthy", "good"];
}

function render() {
  const data = rows();
  const avgAdoption = average(data, "adoption");
  const avgSuccess = average(data, "taskSuccess");
  const avgSla = average(data, "sla");
  const openDefects = data.reduce((sum, row) => sum + row.defects, 0);
  const previousAdoption = average(data, "previousAdoption");
  const adoptionDelta = avgAdoption - previousAdoption;

  const cards = [
    { label: "Product adoption", value: formatPercent(avgAdoption), note: `${adoptionDelta >= 0 ? "+" : ""}${adoptionDelta.toFixed(1)} pts vs previous period` },
    { label: "Task success", value: formatPercent(avgSuccess), note: "Core journey completion across digital services" },
    { label: "SLA attainment", value: formatPercent(avgSla), note: "Operational reliability for customer-facing products" },
    { label: "Open defects", value: openDefects.toString(), note: "QA issues tracked for weekly reporting" }
  ];

  document.querySelector("#scorecards").innerHTML = cards
    .map((card) => `<article class="scorecard"><span>${card.label}</span><strong>${card.value}</strong><small>${card.note}</small></article>`)
    .join("");

  const healthScores = data.map(health);
  const avgHealth = healthScores.reduce((sum, score) => sum + score, 0) / Math.max(healthScores.length, 1);
  document.querySelector("#healthBadge").textContent = `${Math.round(avgHealth)} overall health`;

  document.querySelector("#productTable").innerHTML = data
    .map((product) => {
      const score = health(product);
      const [label, className] = statusFor(product);
      return `
        <tr>
          <td><strong>${product.name}</strong><br><small>${product.owner}</small></td>
          <td>${formatPercent(product.adoption)}</td>
          <td>${formatPercent(product.taskSuccess)}</td>
          <td>${product.defects}</td>
          <td>${formatPercent(product.sla)}</td>
          <td><div class="health-bar" aria-label="${score} health score"><span style="width:${score}%"></span></div><span class="status ${className}">${label}</span></td>
        </tr>
      `;
    })
    .join("");

  const risks = [...data]
    .sort((a, b) => b.incidents + b.defects / 10 - (a.incidents + a.defects / 10))
    .slice(0, 3);
  document.querySelector("#riskQueue").innerHTML = risks
    .map((product) => {
      const [label, className] = statusFor(product);
      return `<article class="risk-card"><strong>${product.name}<span class="status ${className}">${label}</span></strong><small>${product.defects} defects, ${product.incidents} incidents, ${formatPercent(product.sla)} SLA</small></article>`;
    })
    .join("");

  document.querySelector("#workflow").innerHTML = workflows
    .map(([title, body]) => `<li><strong>${title}</strong><small>${body}</small></li>`)
    .join("");

  const drivers = [
    ["Adoption movement", "Track monthly active use and completion of priority workflows by product."],
    ["Quality signals", "Monitor defects, incident volume, SLA, release readiness, and QA exceptions."],
    ["Stakeholder actions", "Translate dashboard changes into owners, timelines, decisions, and follow-up reporting."],
    ["Product operations", "Use a consistent metric dictionary so teams compare the same definitions each week."]
  ];
  document.querySelector("#driverGrid").innerHTML = drivers
    .map(([title, body]) => `<article class="driver"><strong>${title}</strong><small>${body}</small></article>`)
    .join("");
}

productFilter.addEventListener("change", render);
periodFilter.addEventListener("change", render);
render();
