import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';
import { loginUser, registerUser } from '../services/api';

export function AuthModal({ onAuthSuccess }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password.trim()) {
      setError('Email and password are required.');
      return;
    }

    if (!isLogin && password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (!isLogin && password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    setSubmitting(true);
    try {
      if (isLogin) {
        const data = await loginUser(email, password);
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        onAuthSuccess(data.user);
      } else {
        await registerUser(email, password);
        // Automatically login after successful registration
        const data = await loginUser(email, password);
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        onAuthSuccess(data.user);
      }
    } catch (err) {
      console.error('Auth error:', err);
      const msg = err.response?.data?.detail || 'Authentication failed. Please check your credentials.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4">
      <div className="bg-[#151515] rounded-sm border border-[#2D2D2D] max-w-md w-full p-8 shadow-2xl space-y-6">
        
        {/* Editorial Brand Header */}
        <div>
          <div className="font-mono text-xs text-[#707070] uppercase tracking-widest">PRAGATI BHARATI</div>
          <h2 className="text-xl font-semibold text-white tracking-tight mt-1">
            {isLogin ? 'SIGN IN' : 'CREATE ACCOUNT'}
          </h2>
          <div className="border-t border-[#242424] my-3"></div>
          <p className="text-xs text-[#A0A0A0]">
            {isLogin
              ? 'Enter your credentials to access your document studio.'
              : 'Register to start managing and extracting questions.'}
          </p>
        </div>

        {/* Error alert */}
        {error && (
          <div className="p-3 bg-[#111111] border border-[#2D2D2D] text-[#F87171] font-mono text-xs rounded-sm">
            ! {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block font-mono text-xs uppercase tracking-wider text-[#A0A0A0] mb-1">
              EMAIL ADDRESS
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
              className="w-full font-mono text-xs px-3.5 py-2.5 bg-[#111111] border border-[#2D2D2D] text-[#F5F5F5] placeholder-[#707070] rounded-sm focus:outline-none focus:border-[#707070] transition-colors"
            />
          </div>

          <div>
            <label className="block font-mono text-xs uppercase tracking-wider text-[#A0A0A0] mb-1">
              PASSWORD
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full font-mono text-xs pl-3.5 pr-10 py-2.5 bg-[#111111] border border-[#2D2D2D] text-[#F5F5F5] placeholder-[#707070] rounded-sm focus:outline-none focus:border-[#707070] transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#707070] hover:text-[#F5F5F5] transition-colors focus:outline-none cursor-pointer"
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {!isLogin && (
            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-[#A0A0A0] mb-1">
                CONFIRM PASSWORD
              </label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full font-mono text-xs pl-3.5 pr-10 py-2.5 bg-[#111111] border border-[#2D2D2D] text-[#F5F5F5] placeholder-[#707070] rounded-sm focus:outline-none focus:border-[#707070] transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#707070] hover:text-[#F5F5F5] transition-colors focus:outline-none cursor-pointer"
                  title={showConfirmPassword ? 'Hide password' : 'Show password'}
                >
                  {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full text-xs font-semibold uppercase tracking-wider bg-white text-black py-3 rounded-sm hover:bg-[#E5E5E5] transition-colors disabled:bg-[#242424] disabled:text-[#707070]"
          >
            {submitting ? 'PROCESSING...' : isLogin ? 'SIGN IN' : 'CREATE ACCOUNT'}
          </button>
        </form>

        {/* Toggle Login/Register */}
        <div className="text-center font-mono text-xs text-[#707070] pt-2 border-t border-[#242424]">
          {isLogin ? (
            <span>
              DON'T HAVE AN ACCOUNT?{' '}
              <button
                type="button"
                onClick={() => {
                  setIsLogin(false);
                  setError(null);
                }}
                className="font-semibold text-white underline hover:text-[#A0A0A0]"
              >
                REGISTER
              </button>
            </span>
          ) : (
            <span>
              ALREADY HAVE AN ACCOUNT?{' '}
              <button
                type="button"
                onClick={() => {
                  setIsLogin(true);
                  setError(null);
                }}
                className="font-semibold text-white underline hover:text-[#A0A0A0]"
              >
                SIGN IN
              </button>
            </span>
          )}
        </div>

      </div>
    </div>
  );
}


