import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { authService } from "../services/auth.service";

export function ForgotPasswordPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [animate, setAnimate] = useState(false);

  useEffect(() => {
    setAnimate(true);
  }, []);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");

    try {
      setIsSubmitting(true);
      await authService.forgotPassword({
        email,
      });

      navigate("/verify-otp", {
        state: {
          email,
        },
      });
    } catch {
      setError("Unable to send OTP. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen w-full grid grid-cols-1 md:grid-cols-12 bg-[#BDDDFC] relative overflow-hidden font-sans">
      {/* Soft floating background design blobs for Stormy Morning visual depth */}
      <div className="absolute -top-20 -left-20 w-[60vw] h-[60vw] bg-[#6A89A7]/25 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[50vw] h-[50vw] bg-[#88BDF2]/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute top-1/3 right-1/4 w-[40vw] h-[40vw] bg-[#384959]/5 rounded-full blur-[100px] pointer-events-none" />
      
      {/* Decorative background lines for tech-human synthesis overlay */}
      <svg className="absolute inset-0 w-full h-full stroke-[#6A89A7]/15 pointer-events-none" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M-100,200 C300,100 500,400 900,200" strokeWidth="2.5" strokeDasharray="8 8" />
        <path d="M100,500 C400,300 600,600 1100,400" strokeWidth="2" />
      </svg>

      {/* Left Column: Hero Copy & SaaS Illustration (Hidden on Mobile) */}
      <div className="hidden md:flex md:col-span-5 flex-col justify-between p-8 lg:p-12 xl:p-14 relative bg-[#384959] border-r border-[#384959]/20 backdrop-blur-[3px]">
        {/* Soft subtle glow spot in Left Column */}
        <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-[#6A89A7]/15 rounded-full blur-[85px] pointer-events-none" />

        {/* Branding header in the Hero panel */}
        <div className={`flex items-center gap-3 transition-all duration-700 delay-100 z-10 ${
          animate ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-4"
        }`}>
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-[#6A89A7] to-[#88BDF2] text-white shadow-md shadow-[#6A89A7]/20">
            <svg className="w-5.5 h-5.5 text-[#BDDDFC]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <div>
            <span className="font-extrabold tracking-tight text-[#BDDDFC] text-base">Talent Finder</span>
            <span className="block text-[9px] text-[#88BDF2] font-bold tracking-wider uppercase leading-none mt-0.5">
              AI Recruitment Platform
            </span>
          </div>
        </div>

        {/* Hero copy and illustration container (tight spacing for cohesive connection) */}
        <div className="flex-1 flex flex-col justify-center py-4 z-10">
          <div className={`transition-all duration-700 delay-200 ${
            animate ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
          }`}>
            <span className="text-[9px] font-bold tracking-[0.25em] text-[#88BDF2] uppercase block mb-1.5">
              AI Recruitment Platform
            </span>
            <h1 className="text-3xl lg:text-4xl font-black tracking-tight text-[#BDDDFC] leading-tight">
              Reset your password.
            </h1>
            <p className="text-[#BDDDFC]/85 text-xs lg:text-sm leading-relaxed mt-3 max-w-sm">
              Enter your registered email address and we'll send you a verification code.
            </p>
          </div>

          {/* SaaS Illustration in Stormy Morning Theme */}
          <div className={`flex items-center justify-center mt-3 lg:mt-5 transition-all duration-1000 ease-out delay-300 ${
            animate ? "opacity-100 scale-100" : "opacity-0 scale-95"
          }`}>
            <svg viewBox="0 0 500 380" className="w-full max-w-[490px] h-auto drop-shadow-sm" fill="none" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <linearGradient id="stormyBtnGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#6A89A7" />
                  <stop offset="100%" stopColor="#88BDF2" />
                </linearGradient>
                <filter id="softShadow" x="-10%" y="-10%" width="120%" height="120%">
                  <feDropShadow dx="0" dy="5" stdDeviation="7" floodColor="#384959" floodOpacity="0.12" />
                </filter>
              </defs>

              {/* Soft background blobs */}
              <circle cx="260" cy="180" r="140" fill="#6A89A7" fillOpacity="0.15" />
              <circle cx="160" cy="140" r="80" fill="#88BDF2" fillOpacity="0.1" />
              <path d="M 320,100 Q 380,80 400,140 Q 420,200 360,220 Q 300,240 280,180 Q 260,120 320,100 Z" fill="#6A89A7" fillOpacity="0.08" />

              {/* Desk */}
              <rect x="80" y="270" width="340" height="8" rx="4" fill="#6A89A7" fillOpacity="0.4" />
              <line x1="120" y1="278" x2="110" y2="340" stroke="#6A89A7" strokeWidth="4" strokeLinecap="round" opacity="0.6" />
              <line x1="380" y1="278" x2="390" y2="340" stroke="#6A89A7" strokeWidth="4" strokeLinecap="round" opacity="0.6" />

              {/* Recruiter Chair */}
              <path d="M 135,270 L 135,220 A 15,15 0 0 1 150,205 L 160,205" stroke="#384959" strokeWidth="4" strokeLinecap="round" fill="none" opacity="0.8" />
              <line x1="140" y1="270" x2="140" y2="330" stroke="#384959" strokeWidth="4" strokeLinecap="round" opacity="0.8" />
              <line x1="125" y1="330" x2="155" y2="330" stroke="#384959" strokeWidth="4" strokeLinecap="round" opacity="0.8" />

              {/* Recruiter Character */}
              {/* Torso */}
              <path d="M 140,265 C 140,230 180,225 180,265 Z" fill="#6A89A7" />
              {/* Head */}
              <circle cx="160" cy="205" r="16" fill="#BDDDFC" stroke="#6A89A7" strokeWidth="1.5" />
              {/* Hair */}
              <path d="M 144,202 Q 148,185 162,188 Q 174,190 172,208 Q 158,204 144,202 Z" fill="#384959" />
              {/* Arm */}
              <path d="M 165,245 Q 185,245 200,255" stroke="#BDDDFC" strokeWidth="7" strokeLinecap="round" fill="none" />
              
              {/* Laptop */}
              <path d="M 210,270 L 245,270 L 255,250 L 220,250 Z" fill="#6A89A7" fillOpacity="0.8" />
              <path d="M 220,250 L 255,250 L 260,225 L 225,225 Z" fill="#384959" />
              <polygon points="222,248 253,248 257,227 227,227" fill="#BDDDFC" />
              <path d="M 205,270 L 250,270" stroke="#384959" strokeWidth="2" strokeLinecap="round" />

              {/* Floating Match Card 1 */}
              <g transform="translate(240, 45)" filter="url(#softShadow)">
                <rect width="180" height="100" rx="16" fill="white" stroke="#6A89A7" strokeWidth="1" strokeOpacity="0.3" />
                <circle cx="32" cy="32" r="15" fill="#BDDDFC" fillOpacity="0.5" />
                <circle cx="32" cy="30" r="6" fill="#384959" />
                <path d="M 25,40 C 25,35 39,35 39,40" stroke="#384959" strokeWidth="1.5" strokeLinecap="round" fill="none" />
                
                <rect x="58" y="20" width="95" height="7" rx="3.5" fill="#384959" />
                <rect x="58" y="34" width="60" height="5" rx="2.5" fill="#6A89A7" />
                
                <rect x="15" y="66" width="50" height="16" rx="8" fill="#6A89A7" fillOpacity="0.1" />
                <text x="21" y="77" fill="#384959" fontSize="8" fontWeight="bold" fontFamily="sans-serif">Developer</text>

                <rect x="71" y="66" width="38" height="16" rx="8" fill="#88BDF2" fillOpacity="0.15" />
                <text x="79" y="77" fill="#384959" fontSize="8" fontWeight="bold" fontFamily="sans-serif">React</text>

                <rect x="115" y="66" width="50" height="16" rx="8" fill="#BDDDFC" fillOpacity="0.4" />
                <text x="121" y="77" fill="#384959" fontSize="8" fontWeight="bold" fontFamily="sans-serif">98% Match</text>
              </g>

              {/* Floating Review Card 2 */}
              <g transform="translate(290, 175)" filter="url(#softShadow)">
                <rect width="150" height="75" rx="14" fill="white" stroke="#6A89A7" strokeWidth="1" strokeOpacity="0.3" />
                <circle cx="30" cy="30" r="15" fill="#88BDF2" fillOpacity="0.25" />
                <circle cx="30" cy="28" r="6" fill="#384959" />
                <path d="M 24,38 C 24,34 36,34 36,38" stroke="#384959" strokeWidth="1.5" strokeLinecap="round" fill="none" />

                <rect x="55" y="20" width="75" height="6" rx="3" fill="#384959" />
                <rect x="55" y="32" width="45" height="4" rx="2" fill="#6A89A7" />

                <rect x="15" y="48" width="120" height="16" rx="8" fill="url(#stormyBtnGrad)" />
                <text x="36" y="59" fill="white" fontSize="8.5" fontWeight="bold" fontFamily="sans-serif">Schedule Interview</text>
              </g>

              {/* Connections */}
              <path d="M 240,230 C 270,180 250,140 270,110" stroke="#88BDF2" strokeWidth="2" strokeLinecap="round" strokeDasharray="4 4" opacity="0.8" />
              <path d="M 240,240 C 280,240 260,200 285,205" stroke="#6A89A7" strokeWidth="2" strokeLinecap="round" strokeDasharray="4 4" opacity="0.8" />

              {/* Sparks */}
              <path d="M 235,80 L 239,84 L 235,88 L 231,84 Z" fill="#88BDF2" />
              <path d="M 270,160 L 273,163 L 270,166 L 267,163 Z" fill="#6A89A7" />
              <path d="M 435,140 L 438,143 L 435,146 L 432,143 Z" fill="#BDDDFC" />
            </svg>
          </div>
        </div>

        {/* Minimal Footer text in hero */}
        <div className={`text-[#BDDDFC]/50 text-xs transition-all duration-700 delay-400 z-10 ${
          animate ? "opacity-100" : "opacity-0"
        }`}>
          © {new Date().getFullYear()} Talent Finder Inc.
        </div>
      </div>

      {/* Right Column: Centered Form Card (Soft Blue #BDDDFC background panel) */}
      <div className="col-span-1 md:col-span-7 flex flex-col items-center justify-center p-6 sm:p-10 lg:p-14 z-10 relative bg-[#BDDDFC]">
        <div 
          className={`w-full max-w-[440px] transition-all duration-700 ease-out ${
            animate ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
          }`}
        >
          {/* Logo treatment shown on right side */}
          <div className="flex flex-col items-center text-center mb-8">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-[#6A89A7] to-[#88BDF2] text-white shadow-md shadow-[#6A89A7]/10 mb-3.5 hover:scale-105 transition-transform duration-200">
              <svg className="w-6.5 h-6.5 text-[#BDDDFC]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
            </div>
            <h2 className="text-2xl font-black tracking-tight text-[#384959]">Talent Finder</h2>
            <p className="text-xs text-[#6A89A7] font-bold tracking-wider uppercase leading-none mt-1.5">
              AI Recruitment Workspace
            </p>
          </div>

          {/* Premium White Card (Refined shadow and border) */}
          <div className="w-full bg-white border border-[#6A89A7]/20 rounded-[32px] p-8 sm:p-12 shadow-[0_28px_60px_-15px_rgba(56,73,89,0.15)]">
            <div className="mb-7">
              <h3 className="text-xl font-bold text-[#384959]">Forgot Password</h3>
              <p className="text-xs text-[#6A89A7] mt-1">
                Enter the email on your account and we will send a one-time code.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Email Input Field */}
              <div className="space-y-1.5">
                <label htmlFor="email" className="text-xs font-bold text-[#384959] block">
                  Email Address
                </label>
                <div className="relative">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-[#88BDF2] pointer-events-none">
                    <svg className="w-4.5 h-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </span>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@company.com"
                    className="w-full pl-11 pr-4 py-3.5 bg-slate-50/50 hover:bg-slate-50/80 border border-[#6A89A7]/40 rounded-xl text-sm text-[#384959] placeholder-[#6A89A7]/60 outline-none transition-all duration-200 focus:border-[#384959] focus:bg-white focus:ring-4 focus:ring-[#88BDF2]/20 focus:shadow-[0_0_12px_rgba(106,137,167,0.06)]"
                    required
                  />
                </div>
              </div>

              {/* Error Display */}
              {error && (
                <div className="flex items-start gap-2.5 bg-rose-50 border border-rose-100/80 rounded-xl py-3.5 px-4 text-xs font-semibold text-rose-700 shadow-sm animate-shake">
                  <svg className="w-4.5 h-4.5 shrink-0 text-rose-500 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span>{error}</span>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-[#6A89A7] hover:bg-[#384959] active:scale-[0.98] text-[#BDDDFC] rounded-xl py-4 px-4 font-bold text-sm transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-[#6A89A7]/15 hover:shadow-xl hover:shadow-[#384959]/25 hover:-translate-y-0.5 disabled:opacity-60 disabled:cursor-not-allowed disabled:pointer-events-none cursor-pointer"
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin h-4.5 w-4.5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span>Sending OTP...</span>
                  </>
                ) : (
                  <span>Send OTP</span>
                )}
              </button>
            </form>

            {/* Back to Login Link */}
            <div className="mt-7 border-t border-slate-100 pt-5 text-center">
              <Link to="/login" className="text-xs font-semibold text-[#6A89A7] hover:text-[#384959] transition-colors">
                Back to Login
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}