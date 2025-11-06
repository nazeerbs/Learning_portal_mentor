import { redirect } from 'next/navigation';

export default function Home() {
  redirect('/mentor/dashboard_overview'); // Redirect to the main dashboard
  return null; // This component renders nothing, as it redirects.
}
