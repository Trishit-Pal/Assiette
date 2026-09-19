import { useRef, type CSSProperties, type ReactNode } from 'react'
import { useReducedMotion } from 'framer-motion'

export function Tilt({ children, className = '', strength = 6, style }: { children: ReactNode; className?: string; strength?: number; style?: CSSProperties }) {
  const ref = useRef<HTMLDivElement>(null)
  const reduceMotion = useReducedMotion()
  return <div ref={ref} className={`tilt-surface ${className}`} style={style}
    onPointerMove={event => {
      if (reduceMotion || event.pointerType !== 'mouse' || !ref.current) return
      const rect = ref.current.getBoundingClientRect()
      const x = (event.clientX - rect.left) / rect.width - 0.5
      const y = (event.clientY - rect.top) / rect.height - 0.5
      ref.current.style.transform = `perspective(1100px) rotateX(${-y * strength}deg) rotateY(${x * strength}deg) translateZ(0)`
      ref.current.style.setProperty('--pointer-x', `${(x + 0.5) * 100}%`)
      ref.current.style.setProperty('--pointer-y', `${(y + 0.5) * 100}%`)
    }}
    onPointerLeave={() => { if (ref.current) ref.current.style.transform = 'perspective(1100px) rotateX(0deg) rotateY(0deg)' }}>
    {children}
  </div>
}
