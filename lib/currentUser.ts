// lib/authUser.ts
import {jwtDecode} from 'jwt-decode';

export interface DecodedToken {
  email: string;
  expiry: number;
  [key: string]: any;
}

export function getCurrentUser(): DecodedToken | null {
  try {
    const token = localStorage.getItem('token');
    if (!token) return null;

    const decoded = jwtDecode<DecodedToken>(token);
    
    // Check if token is expired
    const now = Math.floor(Date.now() / 1000);
    if (decoded.expiry < now) {
      localStorage.removeItem('token'); // Clean up
      return null;
    }

    return decoded;
  } catch (err) {
    return null;
  }
}
