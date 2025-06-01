'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { jwtDecode } from 'jwt-decode';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');

    if (!token) {
      router.push('/auth/login');
      return;
    }

    try {
      const decoded = jwtDecode(token);
      setUser(decoded);
    } catch (err) {
      localStorage.removeItem('token');
      router.push('/auth/login');
    }
  }, [router]);

  if (!user) return null; // prevent UI flash while checking

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-4">
        Welcome, {user?.name || 'User'}!
      </h1>

      <button
        onClick={() => {
          localStorage.removeItem('token');
          router.push('/auth/login');
        }}
        className="bg-red-600 text-white px-4 py-2 rounded"
      >
        Logout
      </button>
    </div>
  );
}
