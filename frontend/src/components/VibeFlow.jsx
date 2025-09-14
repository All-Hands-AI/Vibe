import { useEffect, useRef } from 'react'

function VibeFlow() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    
    // Set canvas size
    const resizeCanvas = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    
    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)

    // Vibe particles - creative symbols and shapes
    const vibeSymbols = '✨🎨🌟💫⭐🎭🎪🎨🌈💎🔮🎯🎪✨'
    const symbolArray = vibeSymbols.split('')

    const fontSize = 16
    const columns = canvas.width / (fontSize * 2)

    // Array to store floating particles
    const particles = []
    for (let i = 0; i < columns; i++) {
      particles[i] = {
        y: Math.random() * canvas.height,
        speed: 0.5 + Math.random() * 1.5,
        symbol: symbolArray[Math.floor(Math.random() * symbolArray.length)],
        opacity: 0.3 + Math.random() * 0.4,
        hue: Math.random() * 360
      }
    }

    // Drawing function
    const draw = () => {
      // Check if canvas and context are available
      if (!canvas || !ctx) return
      
      // Dark background with slight transparency for trail effect
      ctx.fillStyle = 'rgba(15, 23, 42, 0.05)'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // Draw floating vibe symbols
      ctx.font = `${fontSize}px monospace`

      // Loop through particles
      for (let i = 0; i < particles.length; i++) {
        const particle = particles[i]
        
        // Create gradient colors for vibes
        const colors = [
          `hsla(${particle.hue}, 70%, 60%, ${particle.opacity})`,
          `hsla(${(particle.hue + 60) % 360}, 70%, 60%, ${particle.opacity * 0.8})`,
          `hsla(${(particle.hue + 120) % 360}, 70%, 60%, ${particle.opacity * 0.6})`
        ]
        
        // Draw symbol with vibrant color
        ctx.fillStyle = colors[i % 3]
        ctx.fillText(
          particle.symbol, 
          i * fontSize * 2, 
          particle.y
        )

        // Move particle down slowly
        particle.y += particle.speed

        // Reset particle to top when it goes off screen
        if (particle.y > canvas.height + fontSize) {
          particle.y = -fontSize
          particle.symbol = symbolArray[Math.floor(Math.random() * symbolArray.length)]
          particle.hue = Math.random() * 360
          particle.opacity = 0.3 + Math.random() * 0.4
        }

        // Occasionally change symbol for variety
        if (Math.random() > 0.995) {
          particle.symbol = symbolArray[Math.floor(Math.random() * symbolArray.length)]
        }
      }
    }

    // Animation loop - slower for a more relaxed vibe
    const interval = setInterval(draw, 100)

    return () => {
      clearInterval(interval)
      window.removeEventListener('resize', resizeCanvas)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0 opacity-30"
      style={{ background: 'transparent' }}
    />
  )
}

export default VibeFlow