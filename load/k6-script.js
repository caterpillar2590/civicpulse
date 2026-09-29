// Load generator for the HPA scale-out demo (§3.3). Ramps up load against
// POST /api/complaints (the endpoint that actually does CPU work: triage +
// a DB write), holds it, then ramps down. Run with:
//
//   k6 run --env BASE_URL=http://civicpulse.local load/k6-script.js
//
// Capture `kubectl get hpa -w` in a second terminal while this runs.

import http from "k6/http";
import { check, sleep } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export const options = {
  stages: [
    { duration: "30s", target: 5 },    // warm up
    { duration: "2m", target: 80 },    // ramp - should push CPU past 60%
    { duration: "3m", target: 80 },    // hold - watch replicas rise
    { duration: "1m", target: 0 },     // ramp down - watch the 5min stabilization window
  ],
  thresholds: {
    http_req_failed: ["rate<0.05"],
  },
};

const SAMPLE_TEXTS = [
  "Burst water main flooding the street since this morning",
  "Streetlight has been broken for two weeks on our block",
  "Garbage has not been collected in over a week here",
  "Large pothole growing bigger every day on the main road",
  "Transformer sparking near the local market, looks dangerous",
];

export default function () {
  const text = SAMPLE_TEXTS[Math.floor(Math.random() * SAMPLE_TEXTS.length)];
  const res = http.post(
    `${BASE_URL}/api/complaints`,
    JSON.stringify({ text, location: "Load test sector" }),
    { headers: { "Content-Type": "application/json" } }
  );
  check(res, {
    "status is 201 or 429": (r) => r.status === 201 || r.status === 429,
  });
  sleep(0.2);
}
