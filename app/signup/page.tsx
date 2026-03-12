'use client'
import React, { useState } from 'react'
import { supabase } from '@/lib/supabase'

export default function SignUp() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSignUp() {
    setLoading(true)
    setError('')

    const { data, error: authError } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { name, phone } }
    })

    if (authError) {
      setError(authError.message)
      setLoading(false)
      return
    }

    // Save to leads table
    await supabase.from('leads').insert({ name, email, phone })

    window.location.href = '/'
  }

  return (
    <main style={{ minHeight: '100vh', background: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
      <div style={{ background: 'white', borderRadius: '12px', padding: '40px', width: '100%', maxWidth: '420px' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>🏠</div>
          <h1 style={{ margin: '0 0 8px', fontSize: '24px', fontWeight: 'bold', color: '#0f172a' }}>New Construction Huntsville</h1>
          <p style={{ margin: 0, color: '#64748b', fontSize: '14px' }}>Get free access to 247+ new construction homes across Huntsville</p>
        </div>

        {error && (
          <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '8px', padding: '12px', marginBottom: '16px', color: '#dc2626', fontSize: '14px' }}>
            {error}
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <input
            placeholder="Full Name"
            value={name}
            onChange={e => setName(e.target.value)}
            style={inputStyle}
          />
          <input
            placeholder="Email Address"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            style={inputStyle}
          />
          <input
            placeholder="Phone Number"
            type="tel"
            value={phone}
            onChange={e => setPhone(e.target.value)}
            style={inputStyle}
          />
          <input
            placeholder="Create Password"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            style={inputStyle}
          />
          <button
            onClick={handleSignUp}
            disabled={loading}
            style={{ background: '#2563eb', color: 'white', border: 'none', borderRadius: '8px', padding: '14px', fontSize: '16px', fontWeight: 'bold', cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}
          >
            {loading ? 'Creating Account...' : 'Get Free Access'}
          </button>
        </div>

        <p style={{ textAlign: 'center', marginTop: '20px', fontSize: '14px', color: '#64748b' }}>
          Already have an account?{' '}
          <a href="/login" style={{ color: '#2563eb', textDecoration: 'none', fontWeight: '600' }}>Log in</a>
        </p>

        <p style={{ textAlign: 'center', marginTop: '16px', fontSize: '12px', color: '#94a3b8' }}>
          By signing up you agree to receive updates about new listings.
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