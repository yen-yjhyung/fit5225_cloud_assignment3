'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { CognitoUser } from 'amazon-cognito-identity-js';
import { userPool } from '@/lib/auth'; // export this from your auth.ts

export default function VerifyEmail() {
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [message, setMessage] = useState('');
  const router = useRouter();

  const handleVerify = () => {
    const user = new CognitoUser({
      Username: email,
      Pool: userPool,
    });

    user.confirmRegistration(code, true, (err, result) => {
      if (err) {
        setMessage(`Error: ${err.message}`);

      } else {
        setMessage(`Success: ${result}`);
        router.push('/auth/login'); // Redirect to login page after verification
      }
    });
  };

  return (
    <div>
      <h2>Verify Email</h2>
      <input type="email" placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
      <input type="text" placeholder="Verification Code" onChange={(e) => setCode(e.target.value)} />
      <button onClick={handleVerify}>Confirm Email</button>
      <p>{message}</p>
    </div>
  );
}
