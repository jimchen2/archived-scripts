// ./FetchUser.js
import Cookies from 'js-cookie';
import { BACKEND_URL } from './config';
// Function to fetch user details from the backend
export const fetchUser = async () => {
  const token = Cookies.get('token');
  try {
    const response = await fetch(`${BACKEND_URL}/auth/validate_token`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    const data = await response.json();
    if (response.ok) {
      return data; // should contain user id and username based on the curl example provided
    } else {
      throw new Error(`Failed to validate token or fetch user details. Status: ${response.status}`);
    }
  } catch (error) {
    console.error('Error fetching user details:', error);
    return null;
  }
};
