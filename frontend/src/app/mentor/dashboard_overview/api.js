/**
 * This file contains the data fetching logic for the mentor dashboard.
 * It uses real backend data if available, otherwise falls back to dynamic mock data.
 */

// --- Dynamic Mock Data Generation ---
function generateDynamicMockData() {
  const baseStudents = [
    { id: 1, name: 'Alice Johnson' },
    { id: 2, name: 'Bob Smith' },
    { id: 3, name: 'Charlie Brown' },
    { id: 4, name: 'Diana Prince' },
    { id: 5, name: 'Eve Wilson' },
    { id: 6, name: 'Frank Miller' },
  ];

  const baseCourses = [
    { id: 1, title: 'React for Beginners', level: 'Beginner', image: 'https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=300&h=200&fit=crop' },
    { id: 2, title: 'Advanced Node.js', level: 'Advanced', image: 'https://images.unsplash.com/photo-1627398242454-45a1465c2479?w=300&h=200&fit=crop' },
    { id: 3, title: 'Python Basics', level: 'Beginner', image: 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=300&h=200&fit=crop' },
    { id: 4, title: 'JavaScript Fundamentals', level: 'Intermediate', image: 'https://images.unsplash.com/photo-1579468118864-1b9ea3c0db4a?w=300&h=200&fit=crop' },
    { id: 5, title: 'Database Design', level: 'Intermediate', image: 'https://images.unsplash.com/photo-1544383835-bda2bc66a55d?w=300&h=200&fit=crop' },
    { id: 6, title: 'Machine Learning Intro', level: 'Advanced', image: 'https://images.unsplash.com/photo-1555255707-c07966088b7b?w=300&h=200&fit=crop' },
  ];

  const students = baseStudents.map(student => ({
    ...student,
    coursesEnrolled: Math.floor(Math.random() * 4) + 1,
    progress: Math.floor(Math.random() * 71) + 30,
    lastActivity: new Date(Date.now() - Math.random() * 10 * 24 * 60 * 60 * 1000)
      .toISOString()
      .split('T')[0],
  }));

  const courses = baseCourses.map(course => ({
    ...course,
    students: Math.floor(Math.random() * 15) + 5,
    progress: Math.floor(Math.random() * 101),
  }));
  courses.find(c => c.title === 'Python Basics').progress = 100;

  const evaluations = [
    { id: 1, studentName: students[0].name, course: courses[0].title, assignment: 'Build a Todo App', dueDate: '2023-12-15', status: 'Pending' },
    { id: 2, studentName: students[1].name, course: courses[1].title, assignment: 'API Development Project', dueDate: '2023-12-18', status: 'Pending' },
    { id: 3, studentName: students[3].name, course: courses[3].title, assignment: 'DOM Manipulation Quiz', dueDate: '2023-12-20', status: 'Pending' },
  ];

  const messages = [
    { id: 1, studentName: students[3].name, message: 'Can we review the last assignment?', time: '2h ago' },
    { id: 2, studentName: students[1].name, message: 'I have a question about the project setup.', time: '5h ago' },
    { id: 3, studentName: students[0].name, message: 'Thanks for the feedback!', time: '1d ago' },
  ];

  const sessions = [
    { id: 1, title: 'React Q&A', time: '10:00 AM Today', status: 'LIVE' },
    { id: 2, title: 'Node.js Workshop', time: '2:00 PM Tomorrow', status: null },
  ];

  const studentNameKeys = students.map(s => s.name.split(' ')[0].toLowerCase());
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
  const progressData = months.map(month => {
    const monthData = { month };
    studentNameKeys.forEach(key => {
      monthData[key] = Math.floor(Math.random() * 60) + 10;
    });
    return monthData;
  });

  const engagementData = courses.map(course => ({
    course: course.title,
    timeSpent: Math.floor(Math.random() * 150) + 50,
    interactions: Math.floor(Math.random() * 70) + 20,
  }));

  const insights = { progressData, engagementData };

  const stats = {
    enrolledCourses: students.reduce((sum, s) => sum + s.coursesEnrolled, 0),
    activeCourses: courses.filter(c => c.progress < 100).length,
    completedCourses: courses.filter(c => c.progress === 100).length,
    totalStudents: students.length,
    pendingEvaluations: evaluations.length,
    upcomingSessions: sessions.filter(s => s.status !== 'LIVE').length,
  };

  return { stats, students, courses, evaluations, sessions, messages, insights };
}

// Generate mock data once
const mockData = generateDynamicMockData();

// --- Main Fetching Function ---
export async function getDashboardData() {
  try {
    const [dashboardRes, insightsRes] = await Promise.all([
      fetch("http://localhost:8000/mentor/dashboard"),
      fetch("http://localhost:8000/mentor/dashboard/insights")
    ]);

    if (!dashboardRes.ok || !insightsRes.ok)
      throw new Error("Failed to fetch dashboard data");

    const data = await dashboardRes.json();
    const insights = await insightsRes.json();

    const students = data.students || mockData.students;
    const totalStudents = students.length;

    const stats = {
      ...(data.stats || mockData.stats),
      totalStudents,
    };

    return {
      stats,
      students,
      courses: data.courses || mockData.courses,
      evaluations: data.evaluations || mockData.evaluations,
      sessions: data.sessions || mockData.sessions,
      messages: data.messages || mockData.messages,
      insights: insights || mockData.insights,
    };

  } catch (error) {
    console.warn("⚠️ Using mock data.", error);

    const totalStudents = mockData.students.length;
    const stats = { ...mockData.stats, totalStudents };

    return { ...mockData, stats };
  }
}

