'use client';

import dynamic from 'next/dynamic';
import { useState, useEffect, memo } from 'react';
import Link from 'next/link';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { getDashboardData } from './api';

// Example of a simple hash function to generate a color
const stringToColor = (str) => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  let color = '#';
  for (let i = 0; i < 3; i++) {
    const value = (hash >> (i * 8)) & 0xFF;
    color += ('00' + value.toString(16)).substr(-2);
  }
  return color;
}

// =================================================================================
// 1. STATISTICS COMPONENTS
// =================================================================================
const statItems = [
  { key: 'enrolledCourses', label: 'Enrolled Courses', color: 'text-blue-400', icon: <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg> },
  { key: 'activeCourses', label: 'Active Courses', color: 'text-green-400', icon: <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg> },
  { key: 'completedCourses', label: 'Completed Courses', color: 'text-purple-400', icon: <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg> },
  { key: 'totalStudents', label: 'Total Students', color: 'text-green-400', icon: <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg> },
  { key: 'pendingEvaluations', label: 'Pending Evaluations', color: 'text-yellow-400', icon: <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg> },
  { key: 'upcomingSessions', label: 'Upcoming Sessions', color: 'text-blue-400', icon: <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg> },
];

function StatCard({ label, value, color, icon }) {
  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow-sm border border-gray-700 flex items-center justify-between transition-transform hover:scale-105">
      <div>
        <h3 className="text-sm font-medium text-gray-400 mb-1">{label}</h3>
        <p className={`text-2xl font-bold ${color}`}>{value}</p>
      </div>
      <div className="text-gray-500">
        {icon}
      </div>
    </div>
  );
}

function MentorStatsCards({ stats }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      {statItems.map(item => (
        <StatCard
          key={item.key}
          label={item.label}
          value={stats[item.key]}
          color={item.color}
          icon={item.icon}
        />
      ))}
    </div>
  );
}

// =================================================================================
// 2. LIVE SESSIONS & MESSAGES PANEL
// =================================================================================
function MentorLiveSessionsPanel({ sessions = [], messages = [] }) {
  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow border border-gray-700 flex flex-col gap-6">
      <h2 className="text-xl font-semibold text-gray-100">Student Interactions</h2>
      <div className="bg-gray-900/50 p-4 rounded-lg">
        <h3 className="text-lg font-medium mb-3 text-gray-100">Upcoming Sessions</h3>
        <div className="space-y-3">
          {sessions.length > 0 ? (
            sessions.map((session) => (
              <div key={session.id} className="flex justify-between items-start p-2 rounded-md hover:bg-gray-700/50 transition-colors cursor-pointer">
                <div>
                  <h4 className="font-medium text-gray-100">{session.title}</h4>
                  <p className="text-sm text-gray-400">{session.time}</p>
                </div>
                {session.status && (
                  <span className="flex items-center text-sm px-2 py-1 bg-red-800 text-red-100 rounded">
                    <span className="w-2 h-2 bg-red-400 rounded-full mr-2 animate-pulse"></span>
                    {session.status}
                  </span>
                )}
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-500">No upcoming sessions.</p>
          )}
        </div>
      </div>
      <div className="bg-gray-900/50 p-4 rounded-lg">
        <h3 className="text-lg font-medium mb-3 text-gray-100">Recent Messages</h3>
        {messages.length > 0 ? (
          <div className="space-y-3">
            {messages.map((message) => (
              <div key={message.id} className="p-2 rounded-md hover:bg-gray-700/50 transition-colors cursor-pointer">
                <div className="flex justify-between items-center">
                  <p className="font-medium text-gray-200 text-sm">{message.studentName}</p>
                  <p className="text-xs text-gray-500">{message.time}</p>
                </div>
                <p className="text-sm text-gray-400 truncate">{message.message}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-8">
            <svg className="w-12 h-12 text-gray-500 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
            <p className="text-gray-500">No new messages.</p>
          </div>
        )}
      </div>
    </div>
  );
}

// =================================================================================
// 3. PENDING EVALUATIONS LIST
// =================================================================================
function MentorEvaluationList({ evaluations = [] }) {
  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow border border-gray-700">
      <h2 className="text-xl font-semibold mb-4 text-gray-100">Pending Evaluations</h2>
      <div className="space-y-4">
        {evaluations.length > 0 ? (
          evaluations.map((evaluation) => (
            <div key={evaluation.id} className="border border-gray-700 rounded-lg p-4 hover:bg-gray-700/50 transition-colors">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="font-medium text-gray-100">{evaluation.studentName}</h3>
                  <p className="text-sm text-gray-400">{evaluation.course} - {evaluation.assignment}</p>
                  <p className="text-xs text-gray-500">Due: {evaluation.dueDate}</p>
                </div>
                <div className="flex items-center gap-2">
                   {/* Contextual AI Action */}
                  <button title="Use AI to draft feedback" className="p-2 text-gray-400 hover:text-blue-400 rounded-md transition-colors">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" /></svg>
                  </button>
                  <span className={`text-sm px-2 py-1 rounded ${evaluation.status === 'Pending' ? 'bg-yellow-800 text-yellow-100' : 'bg-blue-800 text-blue-100'}`}>
                    {evaluation.status}
                  </span>
                  <button className="text-sm bg-blue-600 hover:bg-blue-500 text-white font-semibold py-1 px-3 rounded-md transition-colors">Evaluate</button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <svg className="w-12 h-12 text-gray-500 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <p className="text-gray-400 font-medium">All caught up!</p>
            <p className="text-sm text-gray-500">There are no pending evaluations.</p>
          </div>
        )}
      </div>
    </div>
  );
}

// =================================================================================
// 4. COURSE PROGRESS CARDS
// =================================================================================
function MentorCourseCards({ courses = [] }) {
  const levelColorMap = {
    Beginner: 'bg-green-800 text-green-100',
    Intermediate: 'bg-yellow-800 text-yellow-100',
    Advanced: 'bg-red-800 text-red-100',
  };

  return (
    <div className="w-full">
      <h2 className="text-xl font-semibold mb-4 text-gray-100">Course Progress</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {courses.map((course) => (
          <div key={course.id} className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden hover:border-gray-600 transition-all duration-200 hover:shadow-lg hover:-translate-y-1">
            <div className="relative">
              <img src={course.image} alt={course.title} className="w-full h-32 object-cover" />
              <div className="absolute top-2 right-2">
                <span className={`text-xs px-2 py-1 rounded ${levelColorMap[course.level] || 'bg-gray-700 text-gray-200'}`}>
                  {course.level}
                </span>
              </div>
            </div>
            <div className="p-4">
              <h3 className="font-medium text-gray-100 mb-1">{course.title}</h3>
              <p className="text-xs text-gray-500 mb-2">{course.students} students • Active</p>
              <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
                <div
                  className="bg-blue-400 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${course.progress}%` }}
                ></div>
              </div>
              <p className="text-xs text-gray-400">{course.progress}% Completed</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// =================================================================================
// 5. AI CO-PILOT WIDGET
// =================================================================================
function MentorAICoPilotWidget() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState([
    { text: "Hello! I'm your AI assistant. How can I help you today?", sender: 'ai' }
  ]);

  const toggleModal = () => setIsModalOpen(!isModalOpen);

  const handleSend = () => {
    if (inputValue.trim()) {
      setMessages([...messages, { text: inputValue, sender: 'user' }]);
      setInputValue('');
      setTimeout(() => {
        setMessages(prev => [...prev, { text: "I'm here to help! What else can I assist you with?", sender: 'ai' }]);
      }, 1000);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') handleSend();
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <button onClick={toggleModal} className="bg-gray-700 text-white p-4 rounded-full shadow-lg hover:bg-gray-600 transition-colors">
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" /></svg>
      </button>
      {isModalOpen && (
        <div className="absolute bottom-16 right-0 w-80 bg-gray-800 border border-gray-700 rounded-lg shadow-lg p-4">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold text-gray-100">AI Co-Pilot</h3>
            <button onClick={toggleModal} className="text-gray-400 hover:text-gray-200 text-xl leading-none">×</button>
          </div>
          <div className="mb-3">
            <p className="text-sm text-gray-400 mb-2">Chat with AI for assistance.</p>
            <div className="bg-gray-700 rounded-lg p-3 mb-3 max-h-40 overflow-y-auto">
              {messages.map((message, index) => (
                <div key={index} className={`mb-2 ${message.sender === 'user' ? 'text-right' : 'text-left'}`}>
                  <p className={`text-sm inline-block px-2 py-1 rounded ${message.sender === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-600 text-gray-300'}`}>{message.text}</p>
                </div>
              ))}
            </div>
            <input type="text" value={inputValue} onChange={(e) => setInputValue(e.target.value)} onKeyPress={handleKeyPress} placeholder="Type your message..." className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-gray-500" />
          </div>
          <div className="flex justify-end">
            <button onClick={handleSend} className="px-3 py-1 bg-gray-600 text-white rounded-md text-sm hover:bg-gray-500 transition-colors">Send</button>
          </div>
        </div>
      )}
    </div>
  );
}

// =================================================================================
// 6. INSIGHTS & CHARTS (Dynamically Imported)
// =================================================================================
const renderCustomBarLabel = ({ x, y, width, value }) => {
  if (width < 20) return null;
  return <text x={x + width / 2} y={y + 18} fill="#fff" textAnchor="middle" fontSize="12px">{value}</text>;
};

const CustomizedAxisTick = memo(({ x, y, payload }) => {
  const words = payload.value.split(' ');
  return (
    <g transform={`translate(${x},${y})`}>
      <text x={0} y={0} dy={16} textAnchor="middle" fill="#9CA3AF" fontSize="12px">
        {words.map((word, i) => <tspan key={i} x="0" dy={i > 0 ? '1.2em' : '0'}>{word}</tspan>)}
      </text>
    </g>
  );
});
CustomizedAxisTick.displayName = 'CustomizedAxisTick';

const studentColorMap = { alice: '#10B981', bob: '#3B82F6', charlie: '#F59E0B' }; // Keep a few for consistency, but allow dynamic fallback

function MentorInsightsChartComponent({ insights = { progressData: [], engagementData: [] } }) {
  const { progressData = [], engagementData = [] } = insights;
  const studentKeys = progressData.length > 0 ? Object.keys(progressData[0]).filter(key => key !== 'month') : [];
  return (
    <div className="w-full">
      <h2 className="text-xl font-semibold mb-4 text-gray-100">Mentor Analysis Insights</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-800 p-6 rounded-lg shadow border border-gray-700">
          <h3 className="text-lg font-medium mb-4 text-gray-100">Student Progress Trends</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={progressData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="month" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px', color: '#F9FAFB' }} />
              {studentKeys.map(key => (
                <Line key={key} type="monotone" dataKey={key} stroke={studentColorMap[key] || stringToColor(key)} strokeWidth={2} name={key.charAt(0).toUpperCase() + key.slice(1)} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-gray-800 p-6 rounded-lg shadow border border-gray-700">
          <h3 className="text-lg font-medium mb-10 text-gray-100">Course Engagement Metrics</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={engagementData} margin={{ top: 5, right: 5, left: 0, bottom: 60 }} barCategoryGap="15%" barGap={2}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="course" interval={0} tick={<CustomizedAxisTick />} tickMargin={8} />
              <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '8px', color: '#F9FAFB' }} />
              <Bar dataKey="timeSpent" fill="#10B981" name="Time Spent (min)" label={renderCustomBarLabel} maxBarSize={30} />
              <Bar dataKey="interactions" fill="#3B82F6" name="Interactions" label={renderCustomBarLabel} maxBarSize={30} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

// =================================================================================
// 7. STUDENT OVERVIEW (Dynamically Imported)
// =================================================================================
function formatRelativeTime(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now - date) / 1000);
  const days = Math.floor(diffInSeconds / 86400);
  if (days > 1) return `${days} days ago`;
  if (days === 1) return `1 day ago`;
  const hours = Math.floor(diffInSeconds / 3600);
  if (hours > 1) return `${hours} hours ago`;
  return `Today`;
}

function MentorStudentOverviewComponent({ students = [] }) {
  const totalStudents = students.length;
  const averageProgress = totalStudents > 0 ? Math.round(students.reduce((acc, student) => acc + student.progress, 0) / totalStudents) : 0;
  const midPoint = Math.ceil(students.length / 2);
  const firstColumnStudents = students.slice(0, midPoint);
  const secondColumnStudents = students.slice(midPoint);

  const StudentCard = ({ student }) => (
    <Link href={`/mentor/students/${student.id}`} key={student.id}>
      <div className="border border-gray-700 rounded-lg p-4 hover:bg-gray-700/50 transition-colors cursor-pointer">
        <div className="flex justify-between items-start mb-2">
          <h3 className="font-medium text-gray-100">{student.name}</h3>
          <span className="text-sm text-gray-500">{student.coursesEnrolled} courses</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
          <div className="bg-green-400 h-2 rounded-full" style={{ width: `${student.progress}%` }}></div>
        </div>
        <p className="text-xs text-gray-500">Progress: {student.progress}% | Last Activity: {formatRelativeTime(student.lastActivity)}</p>
      </div>
    </Link>
  );

  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow border border-gray-700">
      <h2 className="text-xl font-semibold mb-4 text-gray-100">Student Overview</h2>
      <div className="mb-4">
        <p className="text-sm text-gray-400">Total Students: {totalStudents}</p>
        <p className="text-sm text-gray-400">Average Progress: {averageProgress}%</p>
      </div>
      <div className="flex space-x-4">
        <div className="flex-1 space-y-4">{firstColumnStudents.map((student) => <StudentCard key={student.id} student={student} />)}</div>
        <div className="flex-1 space-y-4">{secondColumnStudents.map((student) => <StudentCard key={student.id} student={student} />)}</div>
      </div>
    </div>
  );
}

// =================================================================================
// DYNAMIC IMPORTS & MAIN PAGE COMPONENT
// =================================================================================

// Dynamically import heavy components to code-split and reduce initial bundle size.
const MentorInsightsChart = dynamic(() => Promise.resolve(MentorInsightsChartComponent), {
  loading: () => <div className="h-80 w-full bg-gray-800 rounded-lg animate-pulse"></div>
});
const MentorStudentOverview = dynamic(() => Promise.resolve(MentorStudentOverviewComponent), {
  loading: () => <div className="h-96 w-full bg-gray-800 rounded-lg animate-pulse"></div>
});


export default function DashboardOverview() {
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      const dashboardData = await getDashboardData();
      setData(dashboardData);
    };
    fetchData();
  }, []);

  if (!data) {
    return (
      <div className="p-4 md:p-6 animate-pulse">
        <div className="mb-6">
          <div className="h-8 bg-gray-700 rounded w-1/3"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-800 rounded-lg"></div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="h-96 bg-gray-800 rounded-lg"></div>
          <div className="h-96 bg-gray-800 rounded-lg"></div>
        </div>
        <div className="mb-6">
          <div className="h-80 w-full bg-gray-800 rounded-lg"></div>
        </div>
      </div>
    );
  }

  const { stats, students, courses, evaluations, sessions, messages, insights } = data;

  return (
    <div className="p-4 md:p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-100">Dashboard Overview</h1>
      </div>

      {/* Statistics Cards */}
      <MentorStatsCards stats={stats} />

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <MentorLiveSessionsPanel sessions={sessions} messages={messages} />
        <MentorEvaluationList evaluations={evaluations} />
      </div>

      {/* Full Width Insights Chart */}
      <div className="mb-6">
        <MentorInsightsChart insights={insights} />
      </div>

      {/* Full Width Course Progress */}
      <div className="mb-6">
        <MentorCourseCards courses={courses} />
      </div>

      {/* Full Width Student Overview */}
      <div className="mb-6">
        <MentorStudentOverview students={students} />
      </div>

      {/* Floating AI Widget */}
      <MentorAICoPilotWidget />
    </div>
  );
}
