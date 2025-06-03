// /lib/validation/verifyValidation.ts

export interface VerifyForm {
  code: string;
}

export interface VerifyFormErrors {
  code: string;
}

export function validateVerifyForm(form: VerifyForm): {
  isValid: boolean;
  errors: VerifyFormErrors;
} {
  let isValid = true;
  const errors: VerifyFormErrors = {
    code: '',
  };


  if (!form.code.trim()) {
    errors.code = 'Verification code is required';
    isValid = false;
  }

  return { isValid, errors };
}
