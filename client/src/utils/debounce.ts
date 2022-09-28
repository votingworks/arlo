import React, { useEffect } from 'react'

/**
 * Debounces updates to the provided value by delayMs, e.g.
 *
 * const [value, setValue] = useState('value');
 * const [debouncedValue, isDebouncing] = useDebounce(value);
 *
 * console.log(debouncedValue, isDebouncing) --> 'value', false
 * setValue('newValue');
 * console.log(debouncedValue, isDebouncing) --> 'value', true
 *
 * After delayMs...
 *
 * console.log(debouncedValue, isDebouncing) --> 'newValue', false
 */
// eslint-disable-next-line import/prefer-default-export
export function useDebounce<T>(value: T, delayMs = 250): [T, boolean] {
  const [debouncedValue, setDebouncedValue] = React.useState(value)
  const [isDebouncing, setIsDebouncing] = React.useState(false)

  useEffect(() => {
    setIsDebouncing(true)
    const timeout = setTimeout(() => {
      setDebouncedValue(value)
      setIsDebouncing(false)
    }, delayMs)

    return () => {
      clearTimeout(timeout)
    }
  }, [value, delayMs])

  return [debouncedValue, isDebouncing]
}
