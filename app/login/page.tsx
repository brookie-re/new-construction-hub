'use client'
import React, { useState } from 'react'
import { supabase } from '@/lib/supabase'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleLogin() {
    setLoading(true)
    setError('')

    const { error: authError } = await supabase.auth.signInWithPassword({ email, password })

    if (authError) {
      setError(authError.message)
      setLoading(false)
      return
    }

    window.location.href = '/'
  }

  return (
    <main style={{ minHeight: '100vh', background: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
      <div style={{ background: 'white', borderRadius: '12px', padding: '40px', width: '100%', maxWidth: '420px' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>🏠</div>
          <h1 style={{ margin: '0 0 8px', fontSize: '24px', fontWeight: 'bold', color: '#0f172a' }}>Welcome Back</h1>
          <p style={{ margin: 0, color: '#64748b', fontSize: '14px' }}>Log in to access new construction listings</p>
        </div>

        {error && (
          <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', padding: '12px', marginBottom: '16px', color: '#dc2626', fontSize: '14px' }}>
            {error}
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <input
            placeholder="Email Address"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            style={inputStyle}
          />
          <input
            placeholder="Password"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            style={inputStyle}
          />
          <button
            onClick={handleLogin}
            disabled={loading}
            style={{ background: '#2563eb', color: 'white', border: 'none', borderRadius: '8px', padding: '14px', fontSize: '16px', fontWeight: 'bold', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}
          >
            {loading ? 'Logging in...' : 'Log In'}
          </button>
        </div>

        <p style={{ textAlign: 'center', marginTop: '20px', fontSize: '14px', color: '#64748b' }}>
          Don&#39;t have an account?{' '}
          <a href="/signup" style={{ color: '#2563eb', textDecoration: 'none', fontWeight: '600' }}>Sign up free</a>
        </p>
      </div>
    </main>
  )
}

const inputStyle: React.CSSProperties = {
  padding: '12px 16px', borderRadius: '8px',
  border: '1px solid #e2e8f0', fontSize: '15px',
  outline: 'none', width: '100%', boxSizing: 'border-box',
}