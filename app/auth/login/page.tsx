'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { signIn } from '@/lib/auth';

export default function Login() {
  const [form, setForm] = useState({ email: '', password: '' });
  const [message, setMessage] = useState('');
  const router = useRouter();

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    try {
      const { idToken } = await signIn(form.email, form.password);
      localStorage.setItem('token', idToken);
      router.push('/dashboard');
    } catch (err: any) {
      setMessage(`Login failed: ${err}`);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        placeholder="Email"
        required
        onChange={(e) => setForm({ ...form, email: e.target.value })}
      />
      <input
        type="password"
        placeholder="Password"
        required
        onChange={(e) => setForm({ ...form, password: e.target.value })}
      />
      <button type="submit">Login</button>
      <p>{message}</p>

      <p>
        Don't have an account?{' '}
        <Link href="/auth/signup">
          <span style={{ color: 'blue', textDecoration: 'underline', cursor: 'pointer' }}>
            Sign up here
          </span>
        </Link>
      </p>
    </form>
  );
}
