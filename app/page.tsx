'use client'
import React, { useEffect, useRef, useState, useCallback } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { supabase } from '@/lib/supabase'

mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN!

const BUILDERS = ['DR Horton','Lennar','Davidson Homes','Murphy Homes','Valor Communities','Stone Martin Builders','DSLD Homes','Meritage Homes','Smith Douglas Homes','Legacy Homes','Century Communities','Woodland Homes']
const CITIES = ['Huntsville','Madison','Athens','Meridianville','Toney','Harvest','Hazel Green','Owens Cross Roads']

export default function Home() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<mapboxgl.Map | null>(null)
  const markersRef = useRef<{ [id: number]: mapboxgl.Marker }>({})
  const cardRefs = useRef<{ [id: number]: HTMLDivElement | null }>({})
  const mobileCardStripRef = useRef<HTMLDivElement>(null)
  const [listings, setListings] = useState<any[]>([])
  const [communities, setCommunities] = useState<any[]>([])
  const [activeCommunityIds, setActiveCommunityIds] = useState<Set<number>>(new Set())
  const [activeListingId, setActiveListingId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [priceMax, setPriceMax] = useState(1000000)
  const [beds, setBeds] = useState(0)
  const [builder, setBuilder] = useState('')
  const [city, setCity] = useState('')
  const [showMap, setShowMap] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [savedIds, setSavedIds] = useState<Set<number>>(new Set())

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768)
    check()
    window.addEventListener('resize', check)
    return () => window.removeEventListener('resize', check)
  }, [])

  useEffect(() => {
    supabase.from('communities').select('*').then(({ data }) => {
      if (data) setCommunities(data)
    })
  }, [])

  const fetchListings = useCallback(async () => {
    setLoading(true)
    let query = supabase
      .from('listings')
      .select('*, communities(id, name, builder, city, latitude, longitude)')
      .eq('status', 'available')
      .order('price', { ascending: true })
    if (priceMax < 1000000) query = query.lte('price', priceMax)
    if (beds > 0) query = query.gte('beds', beds)
    const { data } = await query
    let filtered = data || []
    if (builder) filtered = filtered.filter((l: any) => l.communities?.builder === builder)
    if (city) filtered = filtered.filter((l: any) => l.communities?.city === city)
    setListings(filtered)
    setActiveCommunityIds(new Set(filtered.map((l: any) => l.community_id)))
    setLoading(false)
  }, [priceMax, beds, builder, city])

  useEffect(() => { fetchListings() }, [fetchListings])

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) window.location.href = '/signup'
    })
  }, [])

  useEffect(() => {
    if (map.current || !mapContainer.current) return
    map.current = new mapboxgl.Map({
      container: mapContainer.current as HTMLElement,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [-86.5861, 34.7304],
      zoom: 10,
    })
    map.current?.addControl(new mapboxgl.NavigationControl(), 'top-right')
  }, [])

  useEffect(() => {
    if (!map.current || communities.length === 0) return
    const currentMap = map.current
    Object.values(markersRef.current).forEach(m => m.remove())
    markersRef.current = {}
    communities.forEach((community) => {
      if (!community.latitude || !community.longitude) return
      const isActive = activeCommunityIds.has(community.id)

      // Price bubble marker
      const el = document.createElement('div')
      const priceLabel = listings.find(l => l.community_id === community.id)
      const price = priceLabel?.price
      el.innerHTML = price
        ? `<div style="background:${isActive ? '#1d4ed8' : '#64748b'};color:white;padding:5px 10px;border-radius:20px;font-size:12px;font-weight:700;white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,0.3);cursor:pointer;border:2px solid white">$${Math.round(price / 1000)}k</div>`
        : `<div style="background:${isActive ? '#1d4ed8' : '#64748b'};color:white;width:12px;height:12px;border-radius:50%;border:2px solid white;box-shadow:0 2px 6px rgba(0,0,0,0.3);cursor:pointer"></div>`

      const marker = new mapboxgl.Marker({ element: el, anchor: 'center' })
        .setLngLat([community.longitude as number, community.latitude as number])
        .addTo(currentMap)

      el.addEventListener('click', () => {
        const first = listings.find(l => l.community_id === community.id)
        if (first) {
          setActiveListingId(first.id)
          if (isMobile) {
            // Scroll mobile card strip to this card
            const idx = listings.findIndex(l => l.community_id === community.id)
            if (mobileCardStripRef.current) {
              const cardWidth = mobileCardStripRef.current.offsetWidth - 48
              mobileCardStripRef.current.scrollTo({ left: idx * (cardWidth + 12), behavior: 'smooth' })
            }
          } else {
            cardRefs.current[first.id]?.scrollIntoView({ behavior: 'smooth', block: 'center' })
          }
          currentMap.flyTo({ center: [community.longitude, community.latitude], zoom: 13, duration: 600 })
        }
      })
      markersRef.current[community.id] = marker
    })
  }, [communities, activeCommunityIds, listings, isMobile])

  function handleCardClick(listing: any) {
    setActiveListingId(listing.id)
    if (map.current && listing.communities?.longitude && listing.communities?.latitude) {
      map.current.flyTo({ center: [listing.communities.longitude, listing.communities.latitude], zoom: 13, duration: 600 })
    }
  }

  function toggleSave(e: React.MouseEvent, id: number) {
    e.stopPropagation()
    setSavedIds(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const ss: React.CSSProperties = {
    padding: '8px 12px', borderRadius: '20px', border: '1px solid #e2e8f0',
    fontSize: '13px', background: 'white', cursor: 'pointer', color: '#1e293b',
    appearance: 'none' as any, WebkitAppearance: 'none', outline: 'none',
    fontWeight: '500'
  }

  // Listing Card — shared between desktop sidebar and mobile strip
  function ListingCard({ listing, compact = false }: { listing: any, compact?: boolean }) {
    const isActive = activeListingId === listing.id
    const isSaved = savedIds.has(listing.id)
    return (
      <div
        ref={(el: HTMLDivElement | null) => { cardRefs.current[listing.id] = el }}
        onClick={() => handleCardClick(listing)}
        style={{
          background: 'white',
          borderRadius: compact ? '12px' : '10px',
          overflow: 'hidden',
          cursor: 'pointer',
          boxShadow: isActive
            ? '0 0 0 2.5px #1d4ed8, 0 4px 20px rgba(29,78,216,0.15)'
            : '0 2px 8px rgba(0,0,0,0.08)',
          transition: 'box-shadow 0.15s',
          flexShrink: 0,
          ...(compact ? { width: 'calc(100vw - 48px)', maxWidth: '340px' } : { margin: '0 12px 12px' })
        }}
      >
        {/* Photo */}
        <div style={{ position: 'relative', height: compact ? '160px' : '190px', background: '#f1f5f9' }}>
          {listing.image_url
            ? <img src={listing.image_url} alt={listing.address} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            : <div style={{ width: '100%', height: '100%', background: 'linear-gradient(135deg,#e2e8f0,#cbd5e1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '32px' }}>🏠</div>
          }
          {/* Save button */}
          <button
            onClick={e => toggleSave(e, listing.id)}
            style={{ position: 'absolute', top: '10px', right: '10px', background: 'white', border: 'none', borderRadius: '50%', width: '32px', height: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', boxShadow: '0 1px 4px rgba(0,0,0,0.2)', fontSize: '16px' }}
          >
            {isSaved ? '❤️' : '🤍'}
          </button>
          {/* New badge */}
          <div style={{ position: 'absolute', top: '10px', left: '10px', background: '#0ea5e9', color: 'white', fontSize: '10px', fontWeight: '700', padding: '3px 8px', borderRadius: '4px', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
            New Build
          </div>
        </div>

        {/* Info */}
        <div style={{ padding: compact ? '10px 12px' : '12px 14px' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '20px', fontWeight: '800', color: '#0f172a', letterSpacing: '-0.5px' }}>
              {listing.price ? '$' + listing.price.toLocaleString() : 'Price N/A'}
            </span>
          </div>

          <div style={{ display: 'flex', gap: '12px', margin: '4px 0', fontSize: '13px', color: '#334155', fontWeight: '500' }}>
            {listing.beds && <span><b>{listing.beds}</b> bd</span>}
            {listing.baths && <span><b>{listing.baths}</b> ba</span>}
            {listing.sqft && <span><b>{listing.sqft?.toLocaleString()}</b> sqft</span>}
          </div>

          <div style={{ fontSize: '13px', color: '#64748b', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {listing.address}
          </div>
          <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {listing.communities?.name} · {listing.communities?.builder}
          </div>

          {!compact && (
            <button
              onClick={e => { e.stopPropagation(); window.location.href = '/community/' + listing.community_id }}
              style={{ marginTop: '10px', width: '100%', background: '#1d4ed8', color: 'white', border: 'none', padding: '9px', borderRadius: '6px', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}
            >
              View Community →
            </button>
          )}
        </div>
      </div>
    )
  }

  return (
    <main style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif' }}>

      {/* ── Filter Bar ── */}
      <div style={{ background: 'white', borderBottom: '1px solid #e2e8f0', padding: '10px 14px', display: 'flex', alignItems: 'center', gap: '8px', zIndex: 10, overflowX: 'auto' }}>
        <span style={{ fontWeight: '800', fontSize: '15px', color: '#0f172a', whiteSpace: 'nowrap', letterSpacing: '-0.3px' }}>🏠 NCH</span>

        <div style={{ display: 'flex', gap: '6px', flex: 1, overflowX: 'auto', padding: '2px 0' }}>
          <select value={priceMax} onChange={e => setPriceMax(Number(e.target.value))} style={ss}>
            <option value={1000000}>Any Price</option>
            <option value={250000}>Under $250k</option>
            <option value={300000}>Under $300k</option>
            <option value={350000}>Under $350k</option>
            <option value={400000}>Under $400k</option>
            <option value={500000}>Under $500k</option>
            <option value={600000}>Under $600k</option>
          </select>
          <select value={beds} onChange={e => setBeds(Number(e.target.value))} style={ss}>
            <option value={0}>Any Beds</option>
            <option value={2}>2+ Beds</option>
            <option value={3}>3+ Beds</option>
            <option value={4}>4+ Beds</option>
            <option value={5}>5+ Beds</option>
          </select>
          <select value={builder} onChange={e => setBuilder(e.target.value)} style={ss}>
            <option value=''>Any Builder</option>
            {BUILDERS.map(b => <option key={b} value={b}>{b}</option>)}
          </select>
          <select value={city} onChange={e => setCity(e.target.value)} style={ss}>
            <option value=''>Any City</option>
            {CITIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        <span style={{ fontSize: '13px', color: '#94a3b8', whiteSpace: 'nowrap', fontWeight: '500' }}>
          {loading ? '...' : `${listings.length} homes`}
        </span>
      </div>

      {/* ── Body ── */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden', position: 'relative' }}>

        {/* Desktop: sidebar cards */}
        {!isMobile && (
          <div style={{ width: '420px', minWidth: '340px', overflowY: 'auto', background: '#f8fafc', borderRight: '1px solid #e2e8f0' }}>
            {loading && <div style={{ padding: '48px', textAlign: 'center', color: '#94a3b8', fontSize: '14px' }}>Loading homes...</div>}
            {!loading && listings.length === 0 && <div style={{ padding: '48px', textAlign: 'center', color: '#94a3b8', fontSize: '14px' }}>No homes match your filters.</div>}
            {!loading && listings.map(listing => <ListingCard key={listing.id} listing={listing} />)}
          </div>
        )}

        {/* Map — always mounted, hidden on mobile list view */}
        <div
          ref={mapContainer}
          style={{
            flex: 1,
            height: '100%',
            display: (isMobile && !showMap) ? 'none' : 'block'
          }}
        />

        {/* ── Mobile: List view ── */}
        {isMobile && !showMap && (
          <div style={{ position: 'absolute', inset: 0, overflowY: 'auto', background: '#f8fafc', paddingBottom: '90px' }}>
            {loading && <div style={{ padding: '48px', textAlign: 'center', color: '#94a3b8', fontSize: '14px' }}>Loading homes...</div>}
            {!loading && listings.length === 0 && <div style={{ padding: '48px', textAlign: 'center', color: '#94a3b8', fontSize: '14px' }}>No homes match your filters.</div>}
            {!loading && listings.map(listing => (
              <div key={listing.id} style={{ margin: '10px 12px' }}>
                <ListingCard listing={listing} />
                {/* View Community button rendered inside card for mobile list */}
                <button
                  onClick={e => { e.stopPropagation(); window.location.href = '/community/' + listing.community_id }}
                  style={{ width: 'calc(100% - 28px)', margin: '-4px 14px 0', background: '#1d4ed8', color: 'white', border: 'none', padding: '10px', borderRadius: '0 0 10px 10px', fontSize: '13px', fontWeight: '600', cursor: 'pointer' }}
                >
                  View Community →
                </button>
              </div>
            ))}
          </div>
        )}

        {/* ── Mobile: Map + bottom card strip (Zillow style) ── */}
        {isMobile && showMap && (
          <div
            ref={mobileCardStripRef}
            style={{
              position: 'absolute',
              bottom: '80px',
              left: 0,
              right: 0,
              display: 'flex',
              gap: '12px',
              overflowX: 'auto',
              padding: '0 24px',
              scrollSnapType: 'x mandatory',
              WebkitOverflowScrolling: 'touch',
              scrollbarWidth: 'none',
              msOverflowStyle: 'none',
              zIndex: 20,
            }}
          >
            {listings.map(listing => (
              <div key={listing.id} style={{ scrollSnapAlign: 'center', flexShrink: 0 }}>
                <ListingCard listing={listing} compact />
                <button
                  onClick={e => { e.stopPropagation(); window.location.href = '/community/' + listing.community_id }}
                  style={{ width: '100%', background: '#1d4ed8', color: 'white', border: 'none', padding: '9px', borderRadius: '0 0 12px 12px', fontSize: '13px', fontWeight: '600', cursor: 'pointer', marginTop: '-1px' }}
                >
                  View Community →
                </button>
              </div>
            ))}
          </div>
        )}

        {/* ── Mobile: Map/List toggle pill ── */}
        {isMobile && (
          <button
            onClick={() => setShowMap(v => !v)}
            style={{
              position: 'fixed', bottom: '24px', left: '50%', transform: 'translateX(-50%)',
              background: '#0f172a', color: 'white', border: 'none', borderRadius: '24px',
              padding: '13px 28px', fontSize: '14px', fontWeight: '700', cursor: 'pointer',
              zIndex: 100, boxShadow: '0 4px 20px rgba(0,0,0,0.35)',
              display: 'flex', alignItems: 'center', gap: '8px', whiteSpace: 'nowrap',
              letterSpacing: '0.2px'
            }}
          >
            {showMap ? '☰ List' : '🗺 Map'}
          </button>
        )}
      </div>
    </main>
  )
}
