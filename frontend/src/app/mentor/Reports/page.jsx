"use client";

import React, { useEffect, useState, useRef } from "react";


export default function ReportsCertificates() {
  const [learners, setLearners] = useState([]);
  const [batches, setBatches] = useState([]);
//   useEffect(() => {
//   async function loadData() {
//     const res = await fetch("/api/data");  // <-- calling our API route
//     const result = await res.json();

//     setLearners(result.data.learners);
//     setBatches(result.data.batches);
//   }
  

//   loadData();
// }, []);

  const [search, setSearch] = useState("");
  const [batchFilter, setBatchFilter] = useState("");
  const [selectedLearners, setSelectedLearners] = useState(new Set());
  const [loading, setLoading] = useState(true);

  const [batchFeedback, setBatchFeedback] = useState({
  "Batch A-2024": "Good progress, strong engagement",
  "Batch B-2024": "Needs improvement in assignment submissions",
  "Batch C-2024": "Excellent participation and completion rate",
  "Batch D-2024": "Learners are improving steadily",
  "Batch E-2024": "Outstanding group, very consistent",
  "Batch F-2024": "Slow progress, requires more support",
});
// ✅ fallback sample data — 6 learners and 6 batches (light theme, card-based UI)
  const SAMPLE_LEARNERS = [
    { id: "L001", name: "Alice Johnson", batchId: "B001", batchName: "Batch A-2024", progress: 95, certificateStatus: "unsigned", completionDate: "2024-10-15", finalScore: 95 },
    { id: "L002", name: "Bob Smith", batchId: "B002", batchName: "Batch B-2024", progress: 65, certificateStatus: "unsigned", completionDate: "2024-09-10", finalScore: 72 },
    { id: "L003", name: "Charlie Brown", batchId: "B003", batchName: "Batch C-2024", progress: 88, certificateStatus: "unsigned", completionDate: "2024-09-28", finalScore: 89 },
    { id: "L004", name: "David Wilson", batchId: "B004", batchName: "Batch D-2024", progress: 70, certificateStatus: "unsigned", completionDate: "2024-08-14", finalScore: 74 },
    { id: "L005", name: "Emily Clark", batchId: "B005", batchName: "Batch E-2024", progress: 98, certificateStatus: "unsigned", completionDate: "2024-10-20", finalScore: 97 },
    { id: "L006", name: "Fiona Davis", batchId: "B006", batchName: "Batch F-2024", progress: 60, certificateStatus: "unsigned", completionDate: "2024-07-05", finalScore: 63 }
  ];

  const SAMPLE_BATCHES = [
    { id: "B001", name: "Batch A-2024", startDate: "2024-01-15", endDate: "2024-06-15", totalLearners: 25, completed: 18, avgProgress: 82 },
    { id: "B002", name: "Batch B-2024", startDate: "2024-03-01", endDate: "2024-08-01", totalLearners: 30, completed: 12, avgProgress: 65 },
    { id: "B003", name: "Batch C-2024", startDate: "2024-04-10", endDate: "2024-09-10", totalLearners: 28, completed: 20, avgProgress: 78 },
    { id: "B004", name: "Batch D-2024", startDate: "2024-02-18", endDate: "2024-07-15", totalLearners: 32, completed: 16, avgProgress: 70 },
    { id: "B005", name: "Batch E-2024", startDate: "2024-05-05", endDate: "2024-10-05", totalLearners: 22, completed: 10, avgProgress: 86 },
    { id: "B006", name: "Batch F-2024", startDate: "2024-01-20", endDate: "2024-05-20", totalLearners: 26, completed: 14, avgProgress: 67 }
  ];

  // ************ FETCH API DATA (tries env; falls back to sample) ************
  useEffect(() => {
    let mounted = true;

    async function fetchData() {
      setLoading(true);
      try {
        if (!process.env.NEXT_PUBLIC_API_URL) throw new Error("no api url");

        const resL = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/learners`, {
          headers: { "x-api-key": process.env.NEXT_PUBLIC_API_KEY }
        });

        const resB = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/batches`, {
          headers: { "x-api-key": process.env.NEXT_PUBLIC_API_KEY }
        });

        if (!mounted) return;

        if (resL.ok && resB.ok) {
          const learnersJson = await resL.json();
          const batchesJson = await resB.json();
          setLearners(learnersJson);
          setBatches(batchesJson);
        } else {
          setLearners(SAMPLE_LEARNERS);
          setBatches(SAMPLE_BATCHES);
        }
      } catch (err) {
        // fallback to sample data when API unavailable
        setLearners(SAMPLE_LEARNERS);
        setBatches(SAMPLE_BATCHES);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    fetchData();
    return () => (mounted = false);
  }, []);
  // ************ END FETCH API ************

  // Stats
  const totalLearners = learners.length;
  const activeBatches = batches.length;
  const pendingCertificates = learners.filter(l => l.certificateStatus === "unsigned").length;
  const avgProgress = learners.length ? Math.round(learners.reduce((s, l) => s + (l.progress || 0), 0) / learners.length) : 0;

  // Search Filter
  const filteredLearners = learners.filter(l =>
    l.name.toLowerCase().includes(search.toLowerCase()) &&
    (batchFilter ? l.batchId === batchFilter : true)
  );

  // Selection handlers (using Set)
  function toggleSelectLearner(id) {
    setSelectedLearners(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function selectAllVisible() {
    setSelectedLearners(new Set(filteredLearners.map(l => l.id)));
  }

  function clearSelection() {
    setSelectedLearners(new Set());
  }

  // Approve / Reject (local optimistic update + backend call)
  async function approveCertificate(id) {
    setLearners(prev => prev.map(l => (l.id === id ? { ...l, certificateStatus: "signed" } : l)));
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/learners/${id}/approve`, { method: "POST", headers: { "x-api-key": process.env.NEXT_PUBLIC_API_KEY } });
    } catch (err) {
      // ignore for sample fallback
    }
  }

  async function rejectCertificate(id) {
    setLearners(prev => prev.map(l => (l.id === id ? { ...l, certificateStatus: "rejected" } : l)));
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/learners/${id}/reject`, { method: "POST", headers: { "x-api-key": process.env.NEXT_PUBLIC_API_KEY } });
    } catch (err) {
      // ignore for sample fallback
    }
  }

  if (loading) return <div className="p-8">Loading dashboard...</div>;

  // ---------- Export helpers (fixed to use Set) ----------
  const exportAllCSV = () => {
    const rows = learners.map(l => ({
      Name: l.name,
      Batch: l.batchName || l.batch || "-",
      Progress: `${l.progress}%`,
      CertificateStatus: l.certificateStatus,
    }));

    const csvHeader = "Name,Batch,Progress,Certificate Status\n";
    const csvRows = rows.map(r => `${escapeCsv(r.Name)},${escapeCsv(r.Batch)},${r.Progress},${r.CertificateStatus}`).join("\n");
    const csvData = csvHeader + csvRows;

    downloadBlob(csvData, "reports_certifications.csv", "text/csv");
  };

  const exportSelectedCSV = () => {
    if (selectedLearners.size === 0) {
      alert("No learners selected.");
      return;
    }

    const rows = learners
      .filter((l) => selectedLearners.has(l.id))
      .map((l) => ({
        Name: l.name,
        Batch: l.batchName || l.batch || "-",
        Progress: `${l.progress}%`,
        CertificateStatus: l.certificateStatus,
      }));

    const csvHeader = "Name,Batch,Progress,Certificate Status\n";
    const csvRows = rows.map(r => `${escapeCsv(r.Name)},${escapeCsv(r.Batch)},${r.Progress},${r.CertificateStatus}`).join("\n");
    const csvData = csvHeader + csvRows;

    downloadBlob(csvData, "selected_learners.csv", "text/csv");
  };

  const exportSelectedPDF = () => {
    if (selectedLearners.size === 0) {
      alert("No learners selected.");
      return;
    }

    const selectedData = learners.filter((l) => selectedLearners.has(l.id));

    const content = selectedData
      .map((l) => `Name: ${l.name}\nBatch: ${l.batchName || l.batch}\nProgress: ${l.progress}%\nCertificate Status: ${l.certificateStatus}\n\n`)
      .join("");

    // Note: creating a real PDF from client requires a library. This produces a .txt-style PDF blob as a simple fallback.
    const blob = new Blob([content], { type: "application/pdf" });
    downloadBlobFromObjectURL(blob, "selected_learners.pdf");
  };

  // Download a batch report CSV (simple per-batch export)
  function downloadBatchReport(batchId) {
    const batch = batches.find(b => b.id === batchId);
    const batchLearners = learners.filter(l => l.batchId === batchId);

    const rows = batchLearners.map(l => ({ Name: l.name, ID: l.id, Progress: `${l.progress}%`, Status: l.certificateStatus }));
    const csvHeader = `Name,ID,Progress,Certificate Status\n`;
    const csvRows = rows.map(r => `${escapeCsv(r.Name)},${r.ID},${r.Progress},${r.Status}`).join("\n");
    const csvData = csvHeader + csvRows;

    downloadBlob(csvData, `${batch ? batch.name.replace(/\s+/g, "_") : batchId}_report.csv`, "text/csv");
  }

  // small utilities
  function escapeCsv(value) {
    if (typeof value !== 'string') return value;
    if (value.includes(',') || value.includes('\n') || value.includes('"')) {
      return '"' + value.replace(/"/g, '""') + '"';
    }
    return value;
  }

  function downloadBlob(data, filename, mimeType) {
    const blob = new Blob([data], { type: mimeType });
    downloadBlobFromObjectURL(blob, filename);
  }

  function downloadBlobFromObjectURL(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  }
// ✅ Add this inside ReportsCertificates() component
const downloadCertificate = (learnerId) => {
  try {
    const certificateURL = `/certificates/${learnerId}.pdf`; // Example path

    const link = document.createElement("a");
    link.href = certificateURL;
    link.download = `Certificate_${learnerId}.pdf`;
    link.click();

    console.log("✅ Certificate downloaded for:", learnerId);
  } catch (error) {
    console.error("❌ Certificate download failed:", error);
  }
};

  // ---------- UI (Light, card-based, Tailwind only, no animations) ----------
 function getFeedbackText(score) {
  if (score >= 90) return "Excellent performance! Strong conceptual understanding.";
  if (score >= 75) return "Good progress. Can continue to improve.";
  if (score >= 60) return "Average performance. Needs improvement.";
  return "Insufficient performance. Further learning required.";
}

  function generateFeedbackReport(learner) {

  const feedback = `
  FEEDBACK REPORT
  
  Learner: ${learner.name}
  Batch: ${learner.batchName}
  Completion Date: ${learner.completionDate}
  Final Score: ${learner.finalScore}%
  Progress: ${learner.progress}%

  Feedback:
  ${getFeedbackText(learner.finalScore)}
  `;

  const blob = new Blob([feedback], { type: "text/plain" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = `${learner.name}-feedback-report.txt`;
  a.click();
  URL.revokeObjectURL(url);
}
const generateBatchFeedbackReport = () => {
  if (!batchFilter) {
    alert("Please select a batch first.");
    return;
  }

  const batchLearners = learners.filter(
    (l) => l.batchName === batchFilter
  );

  if (batchLearners.length === 0) {
    alert("No learners found for this batch.");
    return;
  }

  let report = `=========== BATCH FEEDBACK REPORT ===========

Batch: ${batchFilter}
Total Learners: ${batchLearners.length}

--------------------------------------------
`;

  batchLearners.forEach((learner, index) => {
    const feedbackText =
      learner.finalScore >= 90
        ? "Excellent performance! Shows strong understanding."
        : learner.finalScore >= 75
        ? "Good progress with consistent effort."
        : learner.finalScore >= 60
        ? "Average progress. Improvement recommended."
        : "Below expectation. Needs improvement.";

    report += `
${index + 1}. ${learner.name}
Progress: ${learner.progress}%
Final Score: ${learner.finalScore}%
Feedback: ${feedbackText}
--------------------------------------------
`;
  });

  const blob = new Blob([report], { type: "text/plain" });
  const url = window.URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = `${batchFilter}_BatchFeedbackReport.txt`;
  a.click();
};

  return (
    <div className="p-8 font-sans max-w-7xl mx-auto bg-gray-50 min-h-screen">
      {/* Header */}
      <header className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">Reports & Certifications</h1>
          <p className="text-gray-600 mt-1">Manage learners, validate certificates, and track performance</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-sm text-gray-500">Updated</div>
            <div className="text-sm text-gray-600">Local data · Preview</div>
          </div>
          <button onClick={exportAllCSV} className="px-4 py-2 bg-indigo-600 text-white rounded-md shadow">Export CSV</button>
        </div>
      </header>

      {/* Top summary cards */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-2xl shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-500">Total Learners</div>
              <div className="text-2xl font-bold text-slate-800 mt-1">{totalLearners}</div>
              <div className="text-xs text-gray-400 mt-1">Includes active & archived</div>
            </div>
            <div className="bg-indigo-50 text-indigo-700 p-3 rounded-xl text-xl">👥</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-500">Active Batches</div>
              <div className="text-2xl font-bold text-slate-800 mt-1">{activeBatches}</div>
              <div className="text-xs text-gray-400 mt-1">Current running batches</div>
            </div>
            <div className="bg-indigo-50 text-indigo-700 p-3 rounded-xl text-xl">🎓</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-500">Pending Certificates</div>
              <div className="text-2xl font-bold text-slate-800 mt-1">{pendingCertificates}</div>
              <div className="text-xs text-gray-400 mt-1">Waiting for review</div>
            </div>
            <div className="bg-yellow-50 text-yellow-600 p-3 rounded-xl text-xl">🏷️</div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-500">Avg. Progress</div>
              <div className="text-2xl font-bold text-slate-800 mt-1">{avgProgress}%</div>
              <div className="text-xs text-gray-400 mt-1">Across all learners</div>
            </div>
            <div className="bg-green-50 text-green-600 p-3 rounded-xl text-xl">📈</div>
          </div>
        </div>
      </section>

      {/* Controls + Learner cards */}
<section className="mb-10">

  {/* ✅ HEADING ADDED HERE */}
  <div className="mb-6">
    <h2 className="text-2xl font-semibold text-indigo-700">Learner Certificate Approval</h2>
    <p className="text-sm text-gray-500">Review and approve learner certificates</p>
  </div>

  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-4">
    <div className="flex items-center gap-3">
      <input value={search} onChange={(e) => setSearch(e.target.value)} className="border px-3 py-2 rounded-md w-72 bg-white" placeholder="Search learners..." />

      <select value={batchFilter} onChange={(e) => setBatchFilter(e.target.value)} className="border px-3 py-2 rounded-md bg-white">
        <option value="">All Batches</option>
        {batches.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
      </select>
    </div>

    <div className="flex items-center gap-3">
      <button onClick={selectAllVisible} className="px-3 py-2 bg-white border rounded-md">Select Visible</button>
      <button onClick={clearSelection} className="px-3 py-2 bg-white border rounded-md">Clear</button>
      <button onClick={exportSelectedCSV} className="px-3 py-2 bg-indigo-600 text-white rounded-md">Export Selected CSV</button>
      <button onClick={exportSelectedPDF} className="px-3 py-2 bg-gray-800 text-white rounded-md">Export Selected PDF</button>
    </div>
  </div>

  {/* Learner cards grid */}
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {filteredLearners.map(l => (
      <div key={l.id} className="bg-white rounded-2xl p-5 shadow-sm flex flex-col">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-lg font-semibold text-slate-800">{l.name}</div>
            <div className="text-sm text-gray-500">{l.batchName} · ID: {l.id}</div>
          </div>
          <div className="flex flex-col items-end">
            <label className="flex items-center gap-2 text-sm text-gray-600">
              <input type="checkbox" className="w-4 h-4" checked={selectedLearners.has(l.id)} onChange={() => toggleSelectLearner(l.id)} />
              <span>Select</span>
            </label>
          </div>
        </div>

        <div className="mt-4">
          <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
            <div style={{ width: `${l.progress}%` }} className="h-3 rounded-full bg-pink-600"></div>
          </div>
          <div className="text-sm text-gray-600 mt-2">Progress: {l.progress}%</div>
        </div>

        <div className="mt-4 grid grid-cols-3 gap-4 text-sm text-gray-600">
          <div>
            <div className="text-xs text-gray-400">Certificate ID</div>
            <div className="font-medium">{l.id.replace('L','C')}</div>
          </div>
          <div>
            <div className="text-xs text-gray-400">Completion</div>
            <div className="font-medium">{l.completionDate}</div>
          </div>
          <div>
            <div className="text-xs text-gray-400">Final Score</div>
            <div className={`font-medium ${l.finalScore >= 75 ? 'text-green-600' : 'text-red-600'}`}>{l.finalScore}%</div>
          </div>
        </div>

        <div className="mt-5 flex items-center gap-3">
        {/* ✅ Generate Feedback Report Button */}
<button
  onClick={() => generateFeedbackReport(l)}
  className="mt-3 w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
>
  Generate Feedback Report
</button>

  {/* ✅ If progress 100% or certificate signed -> show Download button */}
  {(l.progress === 100 || l.certificateStatus === "signed") ? (
    <button
      onClick={() => downloadCertificate(l.id)}
      className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-md"
    >
      Download Certificate
    </button>
  ) : (
    <>
      <button
        onClick={() => approveCertificate(l.id)}
        className="flex-1 px-4 py-2 bg-green-500 text-white rounded-md"
      >
        Approve & Sign
      </button>
      <button
        onClick={() => rejectCertificate(l.id)}
        className="px-4 py-2 bg-white border rounded-md"
      >
        Reject
      </button>
    </>
  )}
</div>

      </div>
    ))}
  </div>
</section>

     {/* 🔹 Batch Overview Section (updated same styling as learner cards) */}
<section className="mt-12">
  <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
    <div>
      <h2 className="text-2xl font-semibold text-indigo-700">Batch Overview</h2>
      <p className="text-sm text-gray-600">Monitor batch progress and export per-batch reports</p>
    </div>

    {/* 🔽 Batch filter */}
    <select
      value={batchFilter}
      onChange={(e) => setBatchFilter(e.target.value)}
      className="border px-3 py-2 rounded-md bg-white shadow-sm w-56"
    >
    {batchFilter && (
  <button
    onClick={generateBatchFeedbackReport}
    className="ml-3 px-4 py-2 bg-blue-700 text-white rounded-md hover:bg-blue-800"
  >
    Generate Batch Feedback Report
  </button>
)}

      <option value="">Show All Batches</option>
      {batches.map((b) => (
        <option key={b.id} value={b.id}>{b.name}</option>
      ))}
    </select>
  </div>

  {/* ✅ Same card look as learner cards */}
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {batches
      .filter(batch => batchFilter ? batch.id === batchFilter : true)
      .map((batch) => (
        <div
          key={batch.id}
          className="bg-white border rounded-2xl p-6 shadow-sm hover:shadow-md transition-all duration-200"
        >
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold text-lg text-slate-800">{batch.name}</h3>

            <button
              onClick={() => downloadBatchReport(batch.id)}
              className="text-xs px-3 py-1 bg-indigo-600 text-white rounded-md shadow hover:bg-indigo-700 transition"
            >
              Export CSV
            </button>
          </div>

          <div className="space-y-2 text-sm text-gray-600">
            <div className="flex justify-between">
              <span>Start</span>
              <span className="font-medium text-indigo-600">{batch.startDate}</span>
            </div>

            <div className="flex justify-between">
              <span>End</span>
              <span className="font-medium text-indigo-600">{batch.endDate}</span>
            </div>

            <div className="flex justify-between">
              <span>Total Learners</span>
              <span className="font-medium text-indigo-600">{batch.totalLearners}</span>
            </div>

            <div className="flex justify-between">
              <span>Completed</span>
              <span className="font-medium text-indigo-600">{batch.completed}</span>
            </div>
          </div>

          {/* ✅ Same gradient progress bar as learner cards */}
          <div className="mt-4">
            <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
              <div
                style={{ width: `${batch.avgProgress}%` }}
                className="h-3 rounded-full bg-pink-600"
              ></div>
            </div>
            <p className="text-right text-sm font-medium mt-2 text-indigo-700">
              {batch.avgProgress}%
            </p>
            {/* ✅ Feedback section (only text, no rating) */}
<div className="mt-4 bg-gray-50 border rounded-lg p-3">
  <p className="font-semibold text-gray-800">Feedback</p>
  <p className="text-sm text-gray-600 mt-1">
   {batchFeedback[batch.name] || "No feedback added yet."}
  </p>
</div>

          </div>
        </div>
      ))}
  </div>
</section>
    </div>
  );
}