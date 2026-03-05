'use client'

import { useEffect, useRef, useState } from 'react'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { supabase } from '@/lib/supabase'

mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN

export default function Home() {
  const mapContainer = useRef(null)
  const map = useRef(null)
  const [communities, setCommunities] = useState([])

  useEffect(() => {
    fetchCommunities()
  }, [])

  async function fetchCommunities() {
    const { data } = await supabase.from('communities').select('*')
    if (data) setCommunities(data)
  }

  useEffect(() => {
    if (map.current) return
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [-86.5861, 34.7304], // Huntsville, AL
      zoom: 10
    })

    map.current.addControl(new mapboxgl.NavigationControl())
  }, [])

  useEffect(() => {
    if (!map.current || communities.length === 0) return

    communities.forEach((community) => {
      const popup = new mapboxgl.Popup({ offset: 25 }).setHTML(`
        <div style="color: black; padding: 8px;">
          <h3 style="margin: 0 0 4px; font-weight: bold;">${community.name}</h3>
          <p style="margin: 0 0 4px;">By ${community.builder}</p>
          <p style="margin: 0 0 8px;">From $${community.price_from?.toLocaleString()}</p>
          <a href="/community/${community.id}" style="background: #2563eb; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none;">View Community</a>
        </div>
      `)

      new mapboxgl.Marker({ color: '#2563eb' })
        .setLngLat([community.longitude, community.latitude])
        .setPopup(popup)
        .addTo(map.current)
    })
  }, [communities])

  return (
    <main style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      <div style={{
        position: 'absolute', top: 20, left: 20, zIndex: 10,
        background: 'rgba(0,0,0,0.8)', color: 'white',
        padding: '16px 20px', borderRadius: '8px'
      }}>
        <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 'bold' }}>🏠 New Construction Huntsville</h1>
        <p style={{ margin: '4px 0 0', fontSize: '14px', opacity: 0.7 }}>{communities.length} communities found</p>
      </div>
      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />
    </main>
  )
}
