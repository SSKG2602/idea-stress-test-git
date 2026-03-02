"use client";

import { Radar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
} from "chart.js";

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip);

interface Props {
  breakdown: Record<string, number>;
}

const MAX_CONTRIBUTION: Record<string, number> = {
  market_openness: 2.5,
  moat: 2.0,
  monetization_ease: 2.0,
  entry_barrier: 1.5,
  survival_resilience: 2.0,
};

// Map internal keys → readable labels
const LABELS: Record<string, string> = {
  market_openness:    "Market Openness",
  moat:               "Moat",
  monetization_ease:  "Monetisation Ease",
  entry_barrier:      "Entry Barrier",
  survival_resilience:"Survival",
};

export default function ScoreRadar({ breakdown }: Props) {
  const keys = Object.keys(breakdown);
  const labels = keys.map((k) => LABELS[k] ?? k);
  // Breakdown values are weighted contributions; normalize each to a 0-10 axis.
  const values = keys.map((k) => {
    const max = MAX_CONTRIBUTION[k] ?? 2.0;
    return Math.min(10, Math.max(0, (breakdown[k] / max) * 10));
  });

  const data = {
    labels,
    datasets: [
      {
        label: "Dimension Strength",
        data: values,
        backgroundColor: "rgba(45, 212, 191, 0.18)",
        borderColor: "rgba(103, 232, 249, 0.9)",
        borderWidth: 2,
        pointBackgroundColor: "rgba(16, 185, 129, 1)",
        pointBorderColor: "rgba(236, 254, 255, 0.9)",
        pointBorderWidth: 1,
      },
    ],
  };

  const options = {
    maintainAspectRatio: false,
    scales: {
      r: {
        min: 0,
        max: 10,
        ticks: {
          stepSize: 2,
          backdropColor: "transparent",
          color: "rgba(148, 163, 184, 0.5)",
          z: 10,
          font: { size: 10 },
        },
        grid: { color: "rgba(148,163,184,0.16)" },
        angleLines: { color: "rgba(148,163,184,0.15)" },
        pointLabels: { color: "#cbd5e1", font: { size: 11 } },
      },
    },
    plugins: { tooltip: { enabled: true }, legend: { display: false } },
  };

  return (
    <div className="h-72 w-full">
      <Radar data={data} options={options} />
    </div>
  );
}
