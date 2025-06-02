export interface SignupForm {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface FormErrors {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export function validateSignupForm(form: SignupForm): {
  isValid: boolean;
  errors: FormErrors;
} {
  let isValid = true;
  const errors: FormErrors = {
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  };

  if (!form.name.trim()) {
    errors.name = "Name is required";
    isValid = false;
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!form.email.trim()) {
    errors.email = "Email is required";
    isValid = false;
  } else if (!emailRegex.test(form.email)) {
    errors.email = "Email is invalid";
    isValid = false;
  }

  const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$/;

  if (!form.password) {
    errors.password = "Password is required";
    isValid = false;
  } else if (!passwordRegex.test(form.password)) {
    errors.password =
      "Password must be at least 8 characters and include uppercase, lowercase, number, and special character";
    isValid = false;
  }

  if (!form.confirmPassword) {
    errors.confirmPassword = "Please confirm your password";
    isValid = false;
  } else if (form.password !== form.confirmPassword) {
    errors.confirmPassword = "Passwords do not match";
    isValid = false;
  }

  return { isValid, errors };
}
