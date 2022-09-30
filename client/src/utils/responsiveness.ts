import { useState, useEffect } from 'react'

/**
 * Given a CSS media query, returns whether the media query is matched, e.g.
 *
 * const isDesktopWidth = useMediaQuery('(min-width: 64em)')
 *
 * Listens for updates, e.g. in response to window resizing.
 */
export function useMediaQuery(query: string): boolean {
  const [isMatched, setIsMatched] = useState(false)

  useEffect(() => {
    const matchMedia = window.matchMedia(query)
    setIsMatched(matchMedia.matches)
    const handleChange = () => {
      setIsMatched(matchMedia.matches)
    }
    matchMedia.addEventListener('change', handleChange)
    return () => {
      matchMedia.removeEventListener('change', handleChange)
    }
  }, [query])

  return isMatched
}

/** A breakpoint for mobile vs. tablet */
export const BREAKPOINT_M = '40em'
/** A breakpoint for tablet vs. desktop */
export const BREAKPOINT_L = '64em'

interface IBreakpoints {
  isMobileWidth: boolean
  isTabletWidth: boolean
  isDesktopWidth: boolean
}

/**
 * Returns information about the size of the screen. Listens for updates, e.g. in response to
 * window resizing.
 */
export function useCssBreakpoints(): IBreakpoints {
  const isDesktopWidth = useMediaQuery(`(min-width: ${BREAKPOINT_L})`)
  const isTabletWidth =
    useMediaQuery(`(min-width: ${BREAKPOINT_M})`) && !isDesktopWidth
  const isMobileWidth = !isDesktopWidth && !isTabletWidth

  return {
    isMobileWidth,
    isTabletWidth,
    isDesktopWidth,
  }
}
