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

export function hashBy<T>(
  arr: T[] | null,
  hashFn: (elt: T) => number | string
): string | null {
  return arr && arr.map(hashFn).join(';')
}

export function replaceAtIndex<T>(arr: T[], index: number, newElement: T): T[] {
  return arr
    .slice(0, index)
    .concat([newElement])
    .concat(arr.slice(index + 1))
}

export function range(start: number, stop: number) {
  return [...Array(stop - start + 1)].map((_, i) => start + i)
}
