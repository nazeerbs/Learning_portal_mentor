/**
 * This file contains the data fetching logic for the mentor dashboard.
 * It includes a dynamic mock data generation system that simulates a real-time backend.
 * If the API calls fail, this system provides consistent and interconnected fallback data.
 */

// --- Dynamic Mock Data Generation ---

function generateDynamicMockData() {
  // Base data - The single source of truth
  const baseStudents = [
    { id: 1, name: 'Alice Johnson' }, { id: 2, name: 'Bob Smith' },
    { id: 3, name: 'Charlie Brown' }, { id: 4, name: 'Diana Prince' },
    { id: 5, name: 'Eve Wilson' }, { id: 6, name: 'Frank Miller' },
  ];

  const baseCourses = [
    { id: 1, title: 'React for Beginners', level: 'Beginner', image: 'https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=300&h=200&fit=crop' },
    { id: 2, title: 'Advanced Node.js', level: 'Advanced', image: 'https://images.unsplash.com/photo-1627398242454-45a1465c2479?w=300&h=200&fit=crop' },
    { id: 3, title: 'Python Basics', level: 'Beginner', image: 'https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=300&h=200&fit=crop' },
    { id: 4, title: 'JavaScript Fundamentals', level: 'Intermediate', image: 'https://images.unsplash.com/photo-1579468118864-1b9ea3c0db4a?w=300&h=200&fit=crop' },
    { id: 5, title: 'Database Design', level: 'Intermediate', image: 'https://images.unsplash.com/photo-1544383835-bda2bc66a55d?w=300&h=200&fit=crop' },
    { id: 6, title: 'Machine Learning Intro', level: 'Advanced', image: 'https://images.unsplash.com/photo-1555255707-c07966088b7b?w=300&h=200&fit=crop' },
  ];

  // --- Derived Data ---

  // 1. Generate STUDENTS with dynamic properties
  const students = baseStudents.map(student => ({
    ...student,
    coursesEnrolled: Math.floor(Math.random() * 4) + 1,
    progress: Math.floor(Math.random() * 71) + 30, // Progress between 30% and 100%
    lastActivity: new Date(Date.now() - Math.random() * 10 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // Within last 10 days
  }));

  // 2. Generate COURSES with calculated student counts and progress
  const courses = baseCourses.map(course => ({
    ...course,
    students: Math.floor(Math.random() * 15) + 5, // 5 to 20 students
    progress: Math.floor(Math.random() * 101),
  }));
  courses.find(c => c.title === 'Python Basics').progress = 100; // Ensure one is completed for stats

  // 3. Generate EVALUATIONS from students and courses
  const evaluations = [
    { id: 1, studentName: students[0].name, course: courses[0].title, assignment: 'Build a Todo App', dueDate: '2023-12-15', status: 'Pending' },
    { id: 2, studentName: students[1].name, course: courses[1].title, assignment: 'API Development Project', dueDate: '2023-12-18', status: 'Pending' },
    { id: 3, studentName: students[3].name, course: courses[3].title, assignment: 'DOM Manipulation Quiz', dueDate: '2023-12-20', status: 'Pending' },
  ];

  // 4. Generate MESSAGES from students
  const messages = [
    { id: 1, studentName: students[3].name, message: 'Can we review the last assignment?', time: '2h ago' },
    { id: 2, studentName: students[1].name, message: 'I have a question about the project setup.', time: '5h ago' },
    { id: 3, studentName: students[0].name, message: 'Thanks for the feedback!', time: '1d ago' },
  ];

  // 5. Generate SESSIONS (can remain simple)
  const sessions = [
    { id: 1, title: 'React Q&A', time: '10:00 AM Today', status: 'LIVE' },
    { id: 2, title: 'Node.js Workshop', time: '2:00 PM Tomorrow', status: null },
  ];

  // 6. Generate INSIGHTS from students and courses
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

  // 7. Calculate STATS dynamically
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

// Generate the mock data once
const mockData = generateDynamicMockData();

// --- Generic Fetching Function ---
async function fetchData(endpoint, fallbackData, resourceName) {
  try {
    console.log(`Attempting to fetch ${resourceName} from backend...`);
    const response = await fetch(`https://api.example.com/mentor/${endpoint}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch ${resourceName}: ${response.status} ${response.statusText}`);
    }

    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      throw new Error(`Expected JSON for ${resourceName}, but received ${contentType}`);
    }

    return await response.json();
  } catch (error) {
    console.warn(`⚠️ ${error.message}. Using mock data for ${resourceName} as a fallback.`);
    return fallbackData; // Returns a slice of the pre-generated dynamic mock data
  }
}

// --- Main Data Aggregator ---
export async function getDashboardData() {
  const endpoints = ['stats', 'students', 'courses', 'evaluations', 'sessions', 'messages', 'insights'];

  // Create an array of fetch promises for all endpoints
  const promises = endpoints.map(endpoint =>
    fetchData(endpoint, mockData[endpoint], endpoint)
  );

  // Await all promises to resolve concurrently
  const results = await Promise.all(promises);

  // Dynamically build the final data object from the results
  return endpoints.reduce((acc, endpoint, index) => {
    acc[endpoint] = results[index];
    return acc;
  }, {});
}