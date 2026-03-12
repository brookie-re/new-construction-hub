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
  const [listings, setListings] = useState<any[]>([])
  const [communities, setCommunities] = useState<any[]>([])
  const [activeCommunityIds, setActiveCommunityIds] = useState<Set<number>>(new Set())
  const [activeListingId, setActiveListingId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [priceMax, setPriceMax] = useState(1000000)
  const [beds, setBeds] = useState(0)
  const [builder, setBuilder] = useState('')
  const [city, setCity] = useState('')

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
    if (map.current || !mapContainer.current) return
    map.current = new mapboxgl.Map({
      container: mapContainer.current as HTMLElement,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [-86.5861, 34.7304],
      zoom: 10,
    })
    map.current?.addControl(new mapboxgl.NavigationControl())
  }, [])

  useEffect(() => {
    if (!map.current || communities.length === 0) return
    const currentMap = map.current
    Object.values(markersRef.current).forEach(m => m.remove())
    markersRef.current = {}
    communities.forEach((community) => {
      if (!community.latitude || !community.longitude) return
      const isActive = activeCommunityIds.has(community.id)
      const marker = new mapboxgl.Marker({ color: isActive ? '#2563eb' : '#94a3b8' })
        .setLngLat([community.longitude as number, community.latitude as number])
        .addTo(currentMap)
      marker.getElement().addEventListener('click', () => {
        const first = listings.find(l => l.community_id === community.id)
        if (first) {
          cardRefs.current[first.id]?.scrollIntoView({ behavior: 'smooth', block: 'center' })
          setActiveListingId(first.id)
        }
      })
      markersRef.current[community.id] = marker
    })
  }, [communities, activeCommunityIds, listings])

  useEffect(() => {
  supabase.auth.getSession().then(({ data: { session } }) => {
    if (!session) window.location.href = '/signup'
    })
  }, [])

  function handleCardClick(listing: any) {
    setActiveListingId(listing.id)
    if (map.current && listing.communities?.longitude && listing.communities?.latitude) {
      map.current.flyTo({ center: [listing.communities.longitude, listing.communities.latitude], zoom: 13 })
    }
  }

  const ss: React.CSSProperties = { padding: '8px 12px', borderRadius: '6px', border: '1px solid #e2e8f0', fontSize: '14px', background: 'white', cursor: 'pointer', color: '#1e293b' }

  return (
    <main style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <div style={{ background: 'white', borderBottom: '1px solid #e2e8f0', padding: '12px 20px', display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap', zIndex: 10 }}>
        <span style={{ fontWeight: 'bold', fontSize: '16px' }}>{'🏠 NCH'}</span>
        <select value={priceMax} onChange={e => setPriceMax(Number(e.target.value))} style={ss}>
          <option value={1000000}>{'Any Price'}</option>
          <option value={250000}>{'Under $250k'}</option>
          <option value={300000}>{'Under $300k'}</option>
          <option value={350000}>{'Under $350k'}</option>
          <option value={400000}>{'Under $400k'}</option>
          <option value={500000}>{'Under $500k'}</option>
          <option value={600000}>{'Under $600k'}</option>
        </select>
        <select value={beds} onChange={e => setBeds(Number(e.target.value))} style={ss}>
          <option value={0}>{'Any Beds'}</option>
          <option value={2}>{'2+ Beds'}</option>
          <option value={3}>{'3+ Beds'}</option>
          <option value={4}>{'4+ Beds'}</option>
          <option value={5}>{'5+ Beds'}</option>
        </select>
        <select value={builder} onChange={e => setBuilder(e.target.value)} style={ss}>
          <option value={''}>{'Any Builder'}</option>
          {BUILDERS.map(b => <option key={b} value={b}>{b}</option>)}
        </select>
        <select value={city} onChange={e => setCity(e.target.value)} style={ss}>
          <option value={''}>{'Any City'}</option>
          {CITIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <span style={{ marginLeft: 'auto', fontSize: '14px', color: '#64748b' }}>{loading ? 'Loading...' : listings.length + ' homes'}</span>
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <div style={{ width: '400px', minWidth: '340px', overflowY: 'auto', background: '#f8fafc', borderRight: '1px solid #e2e8f0' }}>
          {loading && <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>{'Loading homes...'}</div>}
          {!loading && listings.length === 0 && <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>{'No homes match your filters.'}</div>}
          {!loading && listings.map((listing) => (
            <div
              key={listing.id}
              ref={(el: HTMLDivElement | null) => { cardRefs.current[listing.id] = el }}
              onClick={() => handleCardClick(listing)}
              style={{ background: activeListingId === listing.id ? '#eff6ff' : 'white', border: activeListingId === listing.id ? '2px solid #2563eb' : '1px solid #e2e8f0', borderRadius: '8px', margin: '12px', cursor: 'pointer', overflow: 'hidden' }}
            >
              {listing.image_url && <img src={listing.image_url} alt={listing.address} style={{ width: '100%', height: '180px', objectFit: 'cover' }} />}
              <div style={{ padding: '12px' }}>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#1e293b' }}>{listing.price ? '$' + listing.price.toLocaleString() : 'Price N/A'}</div>
                <div style={{ fontSize: '13px', color: '#475569', margin: '4px 0' }}>
                  {[listing.beds ? listing.beds + ' bd' : null, listing.baths ? listing.baths + ' ba' : null, listing.sqft ? listing.sqft.toLocaleString() + ' sqft' : null].filter(Boolean).join(' · ')}
                </div>
                <div style={{ fontSize: '13px', color: '#64748b' }}>{listing.address}</div>
                <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>{listing.communities?.name + ' · ' + listing.communities?.builder}</div>
                <div onClick={(e) => { e.stopPropagation(); window.location.href = '/community/' + listing.community_id }} style={{ display: 'inline-block', marginTop: '10px', background: '#2563eb', color: 'white', padding: '6px 14px', borderRadius: '4px', fontSize: '12px', cursor: 'pointer' }}>{'View Community'}</div>
              </div>
            </div>
          ))}
        </div>
        <div ref={mapContainer} style={{ flex: 1, height: '100%' }} />
      </div>
    </main>
  )
}