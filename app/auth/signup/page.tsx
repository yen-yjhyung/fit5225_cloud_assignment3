'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { signUp } from '@/lib/auth';

export default function SignUp() {
  const [form, setForm] = useState({ email: '', password: '', name: ''});
  const [message, setMessage] = useState('');
  const router = useRouter();

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    try {
      const msg = await signUp(form.email, form.password, form.name);
      setMessage(msg);
      router.push('/auth/verify'); // Redirect to verification page
      
    } catch (err: any) {
      setMessage(`Error: ${err}`);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="text" placeholder="Name" required onChange={(e) => setForm({ ...form, name: e.target.value })} />
      <input type="email" placeholder="Email" required onChange={(e) => setForm({ ...form, email: e.target.value })} />
      <input type="password" placeholder="Password" required onChange={(e) => setForm({ ...form, password: e.target.value })} />
      <button type="submit">Sign Up</button>
      <p>{message}</p>
    </form>
  );
}
