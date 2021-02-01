export function isObjectEmpty(object: {}): boolean {
  return Object.keys(object).length === 0
}

export function mapValues<OrigValue, NewValue>(
  object: { [key: string]: OrigValue },
  mapFn: (value: OrigValue, key: string) => NewValue
): { [key: string]: NewValue } {
  return Object.fromEntries(
    Object.entries(object).map(([key, value]) => [key, mapFn(value, key)])
  )
}
