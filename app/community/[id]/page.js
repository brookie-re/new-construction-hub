'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { supabase } from '@/lib/supabase'
import Link from 'next/link'

export default function CommunityPage() {
  const { id } = useParams()
  const [community, setCommunity] = useState(null)
  const [floorPlans, setFloorPlans] = useState([])
  const [listings, setListings] = useState([])
  const [form, setForm] = useState({ name: '', email: '', phone: '', message: '' })
  const [submitted, setSubmitted] = useState(false)

  useEffect(() => {
    fetchCommunity()
    fetchFloorPlans()
    fetchListings()
  }, [id])

  async function fetchCommunity() {
    const { data } = await supabase.from('communities').select('*').eq('id', id).single()
    if (data) setCommunity(data)
  }

  async function fetchFloorPlans() {
    const { data } = await supabase.from('floor_plans').select('*').eq('community_id', id)
    if (data) setFloorPlans(data)
  }
async function fetchListings() {
    const { data } = await supabase.from('listings').select('*').eq('community_id', id).eq('status', 'available')
    if (data) setListings(data)
  }

  async function handleSubmit() {
    await supabase.from('leads').insert([{ ...form, community_id: id }])
    setSubmitted(true)
  }

  if (!community) return <div style={{ padding: 40, color: 'white', background: '#0f172a', minHeight: '100vh' }}>Loading...</div>

  return (
    <div style={{ background: '#0f172a', minHeight: '100vh', color: 'white', fontFamily: 'sans-serif' }}>

      {/* Header */}
      <div style={{ background: '#1e293b', padding: '16px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Link href="/" style={{ color: '#60a5fa', textDecoration: 'none', fontSize: 14 }}>← Back to Map</Link>
        <div style={{ fontSize: 13, color: '#94a3b8' }}>New Construction Huntsville</div>
      </div>

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '40px 24px' }}>

        {/* Hero */}
        <div style={{ marginBottom: 40 }}>
          <div style={{ fontSize: 13, color: '#60a5fa', marginBottom: 8 }}>NEW CONSTRUCTION</div>
          <h1 style={{ fontSize: 36, fontWeight: 'bold', margin: '0 0 8px' }}>{community.name}</h1>
          <p style={{ color: '#94a3b8', margin: '0 0 16px' }}>By <strong style={{ color: 'white' }}>{community.builder}</strong> · {community.city}, {community.state}</p>
          <div style={{ display: 'flex', gap: 16 }}>
            <span style={{ background: '#1e3a5f', color: '#60a5fa', padding: '6px 14px', borderRadius: 20, fontSize: 14 }}>
              From ${community.price_from?.toLocaleString()}
            </span>
            {community.price_to && (
              <span style={{ background: '#1e3a5f', color: '#60a5fa', padding: '6px 14px', borderRadius: 20, fontSize: 14 }}>
                To ${community.price_to?.toLocaleString()}
              </span>
            )}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 40 }}>

          {/* Left Column */}
          <div>
            {/* Description */}
            {community.description && (
              <div style={{ background: '#1e293b', borderRadius: 12, padding: 24, marginBottom: 24 }}>
                <h2 style={{ margin: '0 0 12px', fontSize: 20 }}>About This Community</h2>
                <p style={{ color: '#94a3b8', lineHeight: 1.6, margin: 0 }}>{community.description}</p>
              </div>
            )}

            {/* Homes For Sale */}
<div style={{ background: '#1e293b', borderRadius: 12, padding: 24, marginBottom: 24 }}>
  <h2 style={{ margin: '0 0 20px', fontSize: 20 }}>🏠 Homes For Sale ({listings.length})</h2>
  {listings.length === 0 ? (
    <p style={{ color: '#94a3b8' }}>No available listings at this time.</p>
  ) : (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
      {listings.map(listing => (
        <div key={listing.id} style={{ background: '#0f172a', borderRadius: 8, overflow: 'hidden', border: '1px solid #334155' }}>
          {listing.image_url && (
            <img
              src={listing.image_url}
              alt={listing.address}
              style={{ width: '100%', height: 180, objectFit: 'cover' }}
            />
          )}
          <div style={{ padding: 16 }}>
            <div style={{ fontSize: 22, fontWeight: 'bold', color: '#60a5fa', marginBottom: 4 }}>
              ${listing.price?.toLocaleString()}
            </div>
            <div style={{ fontWeight: 'bold', marginBottom: 8 }}>{listing.address}</div>
            <div style={{ color: '#94a3b8', fontSize: 13 }}>
              {listing.beds && `${listing.beds} bed · `}
              {listing.baths && `${listing.baths} bath · `}
              {listing.sqft && `${listing.sqft?.toLocaleString()} sqft`}
            </div>
          </div>
        </div>
      ))}
    </div>
  )}
</div>

            {/* Floor Plans */}
            <div style={{ background: '#1e293b', borderRadius: 12, padding: 24 }}>
              <h2 style={{ margin: '0 0 20px', fontSize: 20 }}>Floor Plans</h2>
              {floorPlans.length === 0 ? (
                <p style={{ color: '#94a3b8' }}>Floor plans coming soon.</p>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 16 }}>
                  {floorPlans.map(plan => (
                    <div key={plan.id} style={{ background: '#0f172a', borderRadius: 8, padding: 16, border: '1px solid #334155' }}>
                      <div style={{ fontWeight: 'bold', marginBottom: 8 }}>{plan.name}</div>
                      <div style={{ color: '#94a3b8', fontSize: 14 }}>{plan.beds} bed · {plan.baths} bath</div>
                      <div style={{ color: '#94a3b8', fontSize: 14 }}>{plan.sqft?.toLocaleString()} sqft</div>
                      {plan.price && <div style={{ color: '#60a5fa', fontWeight: 'bold', marginTop: 8 }}>${plan.price?.toLocaleString()}</div>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Lead Form */}
          <div style={{ background: '#1e293b', borderRadius: 12, padding: 24, height: 'fit-content', position: 'sticky', top: 24 }}>
            <h2 style={{ margin: '0 0 4px', fontSize: 20 }}>Get More Info</h2>
            <p style={{ color: '#94a3b8', fontSize: 13, margin: '0 0 20px' }}>I'll personally connect you with this community.</p>

            {submitted ? (
              <div style={{ textAlign: 'center', padding: 20 }}>
                <div style={{ fontSize: 32, marginBottom: 12 }}>✅</div>
                <p>Thanks! I'll be in touch shortly.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <input placeholder="Your Name" value={form.name} onChange={e => setForm({...form, name: e.target.value})}
                  style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8, padding: '10px 14px', color: 'white', fontSize: 14 }} />
                <input placeholder="Email Address" value={form.email} onChange={e => setForm({...form, email: e.target.value})}
                  style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8, padding: '10px 14px', color: 'white', fontSize: 14 }} />
                <input placeholder="Phone Number" value={form.phone} onChange={e => setForm({...form, phone: e.target.value})}
                  style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8, padding: '10px 14px', color: 'white', fontSize: 14 }} />
                <textarea placeholder="Any questions?" value={form.message} onChange={e => setForm({...form, message: e.target.value})}
                  rows={3} style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8, padding: '10px 14px', color: 'white', fontSize: 14, resize: 'none' }} />
                <button onClick={handleSubmit}
                  style={{ background: '#2563eb', color: 'white', border: 'none', borderRadius: 8, padding: '12px', fontSize: 15, fontWeight: 'bold', cursor: 'pointer' }}>
                  Request Information
                </button>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  )
}