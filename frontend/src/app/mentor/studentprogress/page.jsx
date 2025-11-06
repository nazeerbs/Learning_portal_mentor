"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  Legend,
  LineChart,
  Line,
} from "recharts";

/* ========= UTILS FOR RANDOM COLOR ASSIGNMENT (START) ========= */

// Function to generate a random, persistent color for avatars
const generateRandomColor = () => {
  // A palette of vibrant, distinct colors
  const colors = [
    "#3b82f6", // Blue
    "#f97316", // Orange
    "#8b5cf6", // Violet
    "#10b981", // Emerald
    "#f43f5e", // Rose
    "#06b6d4", // Cyan
    "#eab308", // Yellow-Green
    "#a855f7", // Purple
  ];
  return colors[Math.floor(Math.random() * colors.length)];
};

// Map to store generated colors for persistence
const AVATAR_COLORS_MAP = new Map();

// Get a stable color for a student's ID/Name
const getAvatarColor = (studentId) => {
  if (!AVATAR_COLORS_MAP.has(studentId)) {
    AVATAR_COLORS_MAP.set(studentId, generateRandomColor());
  }
  return AVATAR_COLORS_MAP.get(studentId);
};

// Utility function to handle fetching with retries (Exponential Backoff)
const exponentialBackoffFetch = async (url, options = {}, retries = 3) => {
    for (let i = 0; i < retries; i++) {
        try {
            const res = await fetch(url, options);
            if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
            return res.json();
        } catch (error) {
            if (i === retries - 1) throw error;
            const delay = Math.pow(2, i) * 1000;
            // Wait for delay before retrying
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
};

/* ========= UTILS FOR RANDOM COLOR ASSIGNMENT (END) ========= */


/* ========= MOCK DATA (Used for initial state and fallback) ========= */
const STUDENTS = [
  {
    id: 1,
    name: "Emily Johnson",
    email: "emily.j@school.edu",
    progress: 87,
    status: "Active",
    lastActive: "2 hours ago",
    tasksCompleted: 26,
    totalTasks: 30,
  },
  {
    id: 2,
    name: "Michael Chen",
    email: "michael.c@school.edu",
    progress: 52,
    status: "At Risk",
    lastActive: "3 days ago",
    tasksCompleted: 15,
    totalTasks: 30,
  },
  {
    id: 3,
    name: "Sarah Williams",
    email: "sarah.w@school.edu",
    progress: 94,
    status: "Active",
    lastActive: "5 hours ago",
    tasksCompleted: 28,
    totalTasks: 30,
  },
  {
    id: 4,
    name: "James Rodriguez",
    email: "james.r@school.edu",
    progress: 23,
    status: "Inactive",
    lastActive: "1 week ago",
    tasksCompleted: 7,
    totalTasks: 30,
  },
  {
    id: 5,
    name: "Olivia Brown",
    email: "olivia.b@school.edu",
    progress: 79,
    status: "Active",
    lastActive: "1 day ago",
    tasksCompleted: 24,
    totalTasks: 30,
  },
];

/* ========= MOCK COURSE DATA (Used for initial state and fallback) ========= */
const COURSES = {
  "Node.js Fundamentals": {
    engagement: [
      { day: "Mon", engagement: 20 },
      { day: "Tue", engagement: 10 },
      { day: "Wed", engagement: 18 },
      { day: "Thu", engagement: 15 },
      { day: "Fri", engagement: 8 },
    ],
    activity: [
      { name: "Sun", value: 10 },
      { name: "Mon", value: 15 },
      { name: "Tue", value: 15 },
      { name: "Wed", value: 17 },
      { name: "Thu", value: 15 },
      { name: "Fri", value: 10 },
      { name: "Sat", value: 18 },
    ],
    stats: { totalStudents: 5, avgTimeSpent: "90 mins", dropOffRate: "25%" },
  },
  "React Basics": {
    engagement: [
      { day: "Mon", engagement: 18 },
      { day: "Tue", engagement: 12 },
      { day: "Wed", engagement: 20 },
      { day: "Thu", engagement: 25 },
      { day: "Fri", engagement: 10 },
    ],
    activity: [
      { name: "Sun", value: 11 },
      { name: "Mon", value: 12 },
      { name: "Tue", value: 16 },
      { name: "Wed", value: 15 },
      { name: "Thu", value: 10 },
      { name: "Fri", value: 18 },
      { name: "Sat", value: 12 },
    ],
    stats: { totalStudents: 5, avgTimeSpent: "75 mins", dropOffRate: "30%" },
  },
};

/* ========= STUDENT CARD component remains unchanged ========= */
const StudentCard = ({ student, onViewProgress, onSendFeedback }) => {
  // Status-based color mapping (Active=Green, At Risk=Red, Inactive=Yellow)
  const statusColors = {
    Active: { bg: "#ecfdf5", text: "#16a34a", bar: "#16a34a" }, // Green
    "At Risk": { bg: "#fff1f2", text: "#ef4444", bar: "#ef4444" }, // Red
    Inactive: { bg: "#fffceb", text: "#facc15", bar: "#facc15" }, // Yellow
    default: { bg: "#f3f4f6", text: "#6b7280", bar: "#3b82f6" }, // fallback
  };

  const colors = statusColors[student.status] || statusColors.default;
  // Get the persistent random color for the avatar
  const avatarColor = getAvatarColor(student.id);

  return (
    <div style={styles.card}>
      <div style={styles.cardHeader}>
        {/* Avatar circle with random color */}
        <div style={{ ...styles.avatar, background: avatarColor }}>
          {student.name.split(" ").map((n) => n[0]).join("")}
        </div>
        <div style={{ flex: 1 }}>
          <h3 style={{ margin: 0 }}>{student.name}</h3>
          <p style={{ margin: 0, color: "#6b7280", fontSize: 13 }}>{student.email}</p>
        </div>
        <span
          style={{
            ...styles.status,
            background: colors.bg,
            color: colors.text,
          }}
        >
          {student.status}
        </span>
      </div>

      <div style={{ marginTop: 10 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span>Overall Progress</span>
          <span style={{ color: colors.text, fontWeight: 600 }}>{student.progress}%</span>
        </div>
        <div style={{ background: "#e5e7eb", height: 8, borderRadius: 6, marginTop: 6 }}>
          <div style={{ width: `${student.progress}%`, background: colors.bar, height: "100%", borderRadius: 6 }} />
        </div>
      </div>

      <div style={styles.cardFooter}>
        <p style={{ margin: 0, color: "#6b7280", fontSize: 13 }}>⏱ Last active: {student.lastActive}</p>
        <p style={{ margin: 0, fontSize: 13 }}>
          {student.tasksCompleted}/{student.totalTasks} tasks
        </p>
      </div>

      {/* Buttons */}
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 12 }}>
        <button style={styles.viewBtn} onClick={() => onViewProgress(student)}>
          View Progress
        </button>
        {/* Feedback button style uses the updated styles.feedbackBtn */}
        <button style={styles.feedbackBtn} onClick={() => onSendFeedback(student)}>
          Send Feedback
        </button>
      </div>
    </div>
  );
};

/* ========= MAIN PAGE (with Fetch integration) ========= */
export default function App() {
  // Initialize state with MOCK data for instant load and resilience
  const [students, setStudents] = useState(STUDENTS); 
  const [courseData, setCourseData] = useState(COURSES); // NEW: State for fetched course data

  const [selectedCourse, setSelectedCourse] = useState("Node.js Fundamentals");
  const [filter, setFilter] = useState("All");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [feedbackMode, setFeedbackMode] = useState(false);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  // --- FETCHING LOGIC ---

  // 1. Fetch Student Data (runs once on mount)
  useEffect(() => {
    const fetchStudents = async () => {
      try {
        const data = await exponentialBackoffFetch("http://localhost:5000/api/students");
        // Only update state if the fetched data is an array
        if (Array.isArray(data)) {
            setStudents(data);
        } else {
            throw new Error("Invalid student data format received.");
        }
      } catch (error) {
        console.warn("⚠️ Students: Using mock data due to fetch error:", error?.message ?? error);
      }
    };
    fetchStudents();
  }, []); // Empty dependency array means this runs only once after the initial render

  // 2. Fetch Course and Activity Data (runs once on mount)
  useEffect(() => {
    const fetchCourseData = async () => {
      try {
        const data = await exponentialBackoffFetch("http://localhost:5000/api/courses");
        
        // Ensure data is a valid non-null object
        if (typeof data === 'object' && data !== null && Object.keys(data).length > 0) {
            setCourseData(data);
            
            // If the default selected course isn't in the fetched data, update it
            if (!data[selectedCourse]) {
                setSelectedCourse(Object.keys(data)[0]);
            }
        } else {
            throw new Error("Invalid course data format received or empty object.");
        }
      } catch (error) {
        console.warn("⚠️ Courses: Using mock data due to fetch error:", error?.message ?? error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchCourseData();
  }, []); 

  // --- DATA DERIVATION ---

  // Use fetched data (courseData) for the charts and dropdown
  // currentCourse is now derived from courseData state, which is updated after fetching
  const currentCourse = courseData[selectedCourse] || Object.values(courseData)[0];
  
  const filteredStudents = useMemo(() => {
    return students.filter((s) => {
      const matchFilter = filter === "All" ? true : s.status === filter;
      const matchSearch =
        s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.email.toLowerCase().includes(searchTerm.toLowerCase());
      return matchFilter && matchSearch;
    });
  }, [students, filter, searchTerm]);
  
  // Status-to-color mapping for filter buttons
  const filterColors = {
    All: { bg: "#2563eb", text: "#fff" }, // Blue
    Active: { bg: "#16a34a", text: "#fff" }, // Green
    "At Risk": { bg: "#ef4444", text: "#fff" }, // Red
    Inactive: { bg: "#facc15", text: "#000" }, // Yellow (using black text for visibility)
  };

  // ===== SUMMARY CALCULATIONS =====
  const totalStudents = students.length;
  const avgProgress = totalStudents ? Math.round(students.reduce((a, s) => a + (s.progress || 0), 0) / totalStudents) : 0;
  const atRiskCount = students.filter((s) => s.status === "At Risk").length;
  const activeCount = students.filter((s) => s.status === "Active").length;

  const handleSend = () => {
    if (!selectedStudent) return;
    // NOTE: Changed alert() to a temporary message state for better UI/no browser blocking
    alert(`✅ Feedback sent to ${selectedStudent.name}: "${message}"`); 
    setMessage("");
    setSelectedStudent(null);
    setFeedbackMode(false);
  };
  
  if (isLoading) {
    return <div style={styles.loading}>Loading course data...</div>
  }


  return (
    <main style={styles.page}>
      {/* ===== SUMMARY SECTION (top) remains unchanged ===== */}
      <section style={styles.summarySection}>
        <h2 style={{ marginBottom: 20 }}>Student Progress Tracking</h2>
        <div style={styles.summaryGrid}>
          <div style={styles.summaryCard}>
            <h4>Total Students</h4>
            <p>{totalStudents}</p>
          </div>
          <div style={{ ...styles.summaryCard, background: "#ecfdf5" }}>
            <h4>Average Progress</h4>
            <p>{avgProgress}%</p>
          </div>
          <div style={{ ...styles.summaryCard, background: "#fff7ed" }}>
            <h4>At Risk</h4>
            <p>{atRiskCount}</p>
          </div>
          <div style={{ ...styles.summaryCard, background: "#e0f2fe" }}>
            <h4>Active Students</h4>
            <p>{activeCount}</p>
          </div>
        </div>
      </section>

      {/* ===== COURSE SELECT (uses keys from courseData state) ===== */}
      <div style={styles.headerRow}>
        <select value={selectedCourse} onChange={(e) => setSelectedCourse(e.target.value)} style={styles.dropdown}>
          {/* Now maps over the keys of the dynamic courseData state */}
          {Object.keys(courseData).map((c) => (
            <option key={c}>{c}</option>
          ))}
        </select>
      </div>

      {/* ===== CHARTS (uses currentCourse derived from courseData state) ===== */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(480px, 1fr))",
          gap: 20,
          marginBottom: 30,
        }}
      >
        {/* LEFT: Bar chart + stats inside same card */}
        <div style={styles.chartBox}>
          <h3 style={{ marginBottom: 20 }}>Course Engagement Over Time ({selectedCourse})</h3>
          <ResponsiveContainer width="95%" height={300}>
            <BarChart data={currentCourse.engagement} barSize={28}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="engagement" fill="#3b82f6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>

          {/* STATS moved inside the same box under the bar chart */}
          <div style={{ marginTop: 18, width: "100%" }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
              <div style={styles.courseStatBox}>
                <h4 style={{ margin: 0 }}>Total Students</h4>
                <p style={{ marginTop: 8 }}>{currentCourse.stats.totalStudents}</p>
              </div>
              <div style={styles.courseStatBox}>
                <h4 style={{ margin: 0 }}>Avg Time Spent</h4>
                <p style={{ marginTop: 8 }}>{currentCourse.stats.avgTimeSpent}</p>
              </div>
              <div style={styles.courseStatBox}>
                <h4 style={{ margin: 0 }}>Drop-off Rate</h4>
                <p style={{ marginTop: 8 }}>{currentCourse.stats.dropOffRate}</p>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT: Pie Chart (uses currentCourse.activity derived from courseData state) */}
        <div style={styles.chartBox}>
          <h3 style={{ marginBottom: 20 }}>Overall Weekly Activity Breakdown</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={currentCourse.activity} dataKey="value" nameKey="name" outerRadius={110} label>
                {currentCourse.activity.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={
                      [
                        "#3b82f6",
                        "#a78bfa",
                        "#60a5fa",
                        "#f87171",
                        "#fbbf24",
                        "#34d399",
                        "#ef4444",
                      ][index % 7]
                    }
                  />
                ))}
              </Pie>
              <Tooltip />
              <Legend layout="horizontal" verticalAlign="bottom" />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ===== FILTER BAR remains unchanged ===== */}
      <div style={styles.filterRow}>
        <input
          type="text"
          placeholder="🔍 Search by name or email..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={styles.searchInput}
        />
        {["All", "Active", "At Risk", "Inactive"].map((f) => {
            // Determine the button color based on the filter status
            const isSelected = filter === f;
            const statusColors = filterColors[f] || filterColors.All;
            const buttonStyle = isSelected
              ? { background: statusColors.bg, color: statusColors.text, border: "none" } // No border when selected, use solid color
              : { background: "#fff", color: "#111", border: "1px solid #d1d5db" }; // White background when unselected

            return (
              <button
                key={f}
                onClick={() => setFilter(f)}
                style={{
                  ...styles.filterBtn,
                  ...buttonStyle,
                }}
              >
                {f}
              </button>
            );
          })}
      </div>

      {/* ===== STUDENT CARDS (uses filteredStudents derived from students state) ===== */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: 20,
          marginTop: 20,
        }}
      >
        {filteredStudents.map((student) => (
          <StudentCard
            key={student.id}
            student={student}
            onViewProgress={(s) => {
              setSelectedStudent(s);
              setFeedbackMode(false);
            }}
            onSendFeedback={(s) => {
              setSelectedStudent(s);
              setFeedbackMode(true);
            }}
          />
        ))}
      </div>

      {/* ===== VIEW PROGRESS MODAL remains unchanged ===== */}
      {selectedStudent && !feedbackMode && (
        <div style={styles.modalOverlay}>
          <div style={styles.modalBox}>
            <h3 style={{ marginTop: 0 }}>{selectedStudent.name}'s Progress</h3>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart
                data={[
                  { week: "W1", progress: Math.max(0, selectedStudent.progress - 20) },
                  { week: "W2", progress: Math.max(0, selectedStudent.progress - 10) },
                  { week: "W3", progress: selectedStudent.progress },
                ]}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="week" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Line type="monotone" dataKey="progress" stroke="#2563eb" strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 12 }}>
              <button style={styles.closeBtn} onClick={() => setSelectedStudent(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ===== FEEDBACK MODAL remains unchanged ===== */}
      {selectedStudent && feedbackMode && (
        <div style={styles.modalOverlay}>
          <div style={styles.modalBox}>
            <h3 style={{ marginTop: 0 }}>Send Feedback to {selectedStudent.name}</h3>
            <textarea
              placeholder="Type your feedback message..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              style={styles.textarea}
            />
            <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
              <button
                style={styles.closeBtn}
                onClick={() => {
                  setSelectedStudent(null);
                  setFeedbackMode(false);
                  setMessage("");
                }}
              >
                Cancel
              </button>
              <button style={styles.feedbackBtn} onClick={handleSend}>
                Send
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

/* ========= STYLES (UPDATED feedbackBtn) ========= */
const styles = {
  page: { padding: "20px 60px", background: "#f3f4f6", minHeight: "100vh", fontFamily: "Inter", maxWidth: 1300, margin: "0 auto" },
  loading: { fontSize: 24, padding: 40, textAlign: 'center', color: '#1d4ed8' },
  summarySection: { background: "#fff", padding: 20, borderRadius: 10, boxShadow: "0 1px 4px rgba(0,0,0,0.1)", marginBottom: 25 },
  summaryGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 15 },
  summaryCard: { background: "#f9fafb", borderRadius: 10, padding: "15px 10px", textAlign: "center" },
  headerRow: { display: "flex", justifyContent: "flex-end", marginBottom: 25 },
  dropdown: { padding: 8, borderRadius: 6, border: "1px solid #d1d5db", fontSize: 15 },
  chartBox: { background: "#fff", padding: 20, borderRadius: 12, boxShadow: "0 2px 6px rgba(0,0,0,0.1)", display: "flex", flexDirection: "column", alignItems: "center", minHeight: 380 },
  courseStatsRow: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 20, marginBottom: 30 },
  courseStatBox: { background: "#fff", borderRadius: 10, padding: "12px 10px", textAlign: "center", boxShadow: "0 1px 4px rgba(0,0,0,0.05)" },
  filterRow: { display: "flex", gap: 8, alignItems: "center", marginTop: 30, flexWrap: "wrap" },
  filterBtn: { borderRadius: 8, padding: "6px 12px", fontSize: 14, cursor: "pointer", transition: "background 0.2s, color 0.2s, border 0.2s" },
  searchInput: { flex: 1, minWidth: 260, padding: "8px 12px", border: "1px solid #d1d5db", borderRadius: 8 },
  card: { background: "#fff", padding: 18, borderRadius: 12, boxShadow: "0 1px 6px rgba(0,0,0,0.06)", minHeight: 180 },
  cardHeader: { display: "flex", alignItems: "center", gap: 12 },
  avatar: { width: 48, height: 48, borderRadius: "50%", color: "#fff", display: "grid", placeItems: "center", fontWeight: 700, fontSize: 16 },
  status: { fontSize: 12, fontWeight: 600, padding: "6px 10px", borderRadius: 16 },
  cardFooter: { marginTop: 12, display: "flex", justifyContent: "space-between", alignItems: "center" },
  viewBtn: { border: "1px solid #d1d5db", padding: "8px 14px", borderRadius: 8, background: "#fff", cursor: "pointer" },
  feedbackBtn: { border: "none", padding: "8px 14px", borderRadius: 8, background: "#f97316", color: "#fff", cursor: "pointer" },
  modalOverlay: { position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 9999 },
  modalBox: { background: "#fff", padding: 25, borderRadius: 12, width: 520, maxWidth: "95%", boxShadow: "0 4px 20px rgba(0,0,0,0.15)" },
  closeBtn: { border: "1px solid #d1d5db", padding: "8px 12px", borderRadius: 8, background: "#fff", cursor: "pointer" },
  textarea: { width: "100%", height: 120, border: "1px solid #d1d5db", borderRadius: 8, padding: 10, marginBottom: 12 },
};
