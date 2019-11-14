/**
 * Yields indexes from 1 through `maximum`.
 */
export function* upTo(maximum: number): IterableIterator<number> {
  for (let i = 1; i <= maximum; i++) {
    yield i
  }
}

/**
 * Yields formatted indexes from 1 through `maximum` that all have the same
 * width padded at the start with '0's.
 *
 * @example
 *
 * ```ts
 * Array.from(formattedUpTo(3)) // ['1', '2', '3']
 * Array.from(formattedUpTo(10)) // ['01', '02', '03', '04', '05', '06', '07'. '08', '09', '10']
 * ```
 */
export function* formattedUpTo(maximum: number): IterableIterator<string> {
  const maxLength = maximum.toString().length

  for (const index of upTo(maximum)) {
    yield index.toString().padStart(maxLength, '0')
  }
}
