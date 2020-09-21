export function groupBy<T extends {}>(
  arr: T[],
  keyFn: (obj: T) => string
): { [group: string]: T[] } {
  return arr.reduce(
    (acc, obj) => {
      const key = keyFn(obj)
      if (!(key in acc)) {
        acc[key] = []
      }
      acc[key].push(obj)
      return acc
    },
    {} as { [group: string]: T[] }
  )
}

export function sortBy<T>(arr: T[], keyFn: (elt: T) => number | string): T[] {
  return arr.slice().sort((a, b) => {
    const keyA = keyFn(a)
    const keyB = keyFn(b)
    if (keyA < keyB) return -1
    if (keyA > keyB) return 1
    return 0
  })
}
