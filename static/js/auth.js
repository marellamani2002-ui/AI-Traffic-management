// AI Traffic Management System - Authentication Client Scripts

document.addEventListener('DOMContentLoaded', () => {
    initPasswordToggles();
    initSignupValidation();
    initForgotPasswordModal();
});

/**
 * Toggle visibility of password input fields
 */
function initPasswordToggles() {
    const toggleButtons = document.querySelectorAll('.password-toggle-btn');

    toggleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const input = document.getElementById(targetId);
            if (!input) return;

            const isPassword = input.getAttribute('type') === 'password';
            input.setAttribute('type', isPassword ? 'text' : 'password');

            // Toggle SVG icon
            const eyeOpen = btn.querySelector('.eye-open');
            const eyeClosed = btn.querySelector('.eye-closed');

            if (eyeOpen && eyeClosed) {
                if (isPassword) {
                    eyeOpen.style.display = 'none';
                    eyeClosed.style.display = 'block';
                    btn.setAttribute('aria-label', 'Hide password');
                } else {
                    eyeOpen.style.display = 'block';
                    eyeClosed.style.display = 'none';
                    btn.setAttribute('aria-label', 'Show password');
                }
            }
        });
    });
}

/**
 * Real-time password validation & match checking for Signup form
 */
function initSignupValidation() {
    const signupForm = document.getElementById('signupForm');
    const passwordInput = document.getElementById('password');
    const confirmInput = document.getElementById('confirm_password');
    const strengthBar = document.getElementById('strengthBar');
    const strengthText = document.getElementById('strengthText');
    const matchStatus = document.getElementById('matchStatus');

    if (!passwordInput) return;

    // Real-time strength calculation
    passwordInput.addEventListener('input', () => {
        const val = passwordInput.value;
        const strength = evaluatePasswordStrength(val);

        if (!strengthBar || !strengthText) return;

        strengthBar.className = 'strength-bar';
        if (val.length === 0) {
            strengthBar.style.width = '0%';
            strengthText.textContent = 'Password strength';
            strengthText.style.color = 'var(--text-muted)';
        } else if (strength <= 1) {
            strengthBar.classList.add('weak');
            strengthText.textContent = 'Weak (Needs 8+ chars, mix of letters & numbers)';
            strengthText.style.color = 'var(--accent-red)';
        } else if (strength === 2) {
            strengthBar.classList.add('medium');
            strengthText.textContent = 'Medium (Add special characters or uppercase)';
            strengthText.style.color = 'var(--accent-amber)';
        } else {
            strengthBar.classList.add('strong');
            strengthText.textContent = 'Strong password';
            strengthText.style.color = 'var(--accent-green)';
        }

        checkPasswordMatch();
    });

    if (confirmInput) {
        confirmInput.addEventListener('input', checkPasswordMatch);
    }

    function checkPasswordMatch() {
        if (!confirmInput || !matchStatus) return;

        const pwd = passwordInput.value;
        const confirm = confirmInput.value;

        if (confirm.length === 0) {
            matchStatus.className = 'match-status';
            matchStatus.textContent = '';
            return;
        }

        matchStatus.classList.add('active');
        if (pwd === confirm) {
            matchStatus.className = 'match-status active success';
            matchStatus.textContent = '✓ Passwords match';
        } else {
            matchStatus.className = 'match-status active error';
            matchStatus.textContent = '✕ Passwords do not match';
        }
    }

    // Client-side submit safeguard
    if (signupForm) {
        signupForm.addEventListener('submit', (e) => {
            const pwd = passwordInput.value;
            const confirm = confirmInput ? confirmInput.value : '';

            if (confirmInput && pwd !== confirm) {
                e.preventDefault();
                alert('Please ensure both passwords match before signing up.');
                confirmInput.focus();
                return;
            }

            if (pwd.length < 6) {
                e.preventDefault();
                alert('Password must be at least 6 characters long.');
                passwordInput.focus();
                return;
            }

            const submitBtn = signupForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = `
                    <svg class="spinner" viewBox="0 0 50 50" style="width:18px;height:18px;animation:spin 1s linear infinite;">
                        <circle cx="25" cy="25" r="20" fill="none" stroke="currentColor" stroke-width="5" stroke-dasharray="80" stroke-dashoffset="60"></circle>
                    </svg>
                    Creating Account...
                `;
            }
        });
    }
}

/**
 * Password strength scoring: 0-3
 */
function evaluatePasswordStrength(password) {
    let score = 0;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
    if (/[0-9]/.test(password) || /[^A-Za-z0-9]/.test(password)) score++;
    return score;
}

/**
 * Handle Forgot Password modal popup
 */
function initForgotPasswordModal() {
    const forgotLink = document.getElementById('forgotPasswordLink');
    const modal = document.getElementById('forgotPasswordModal');
    const closeBtn = document.getElementById('closeModalBtn');

    if (!forgotLink || !modal || !closeBtn) return;

    forgotLink.addEventListener('click', (e) => {
        e.preventDefault();
        modal.classList.add('active');
    });

    closeBtn.addEventListener('click', () => {
        modal.classList.remove('active');
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
}
