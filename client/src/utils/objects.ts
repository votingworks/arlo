export function isObjectEmpty(object: {}): boolean {
  return Object.keys(object).length === 0
}

interface IEqualityObject {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any
}

export function isObjectEqual(
  object1: IEqualityObject,
  object2: IEqualityObject
): boolean {
  if (object1 === object2) return true

  const keys1 = Object.keys(object1)
  const keys2 = Object.keys(object2)

  if (keys1.length !== keys2.length) return false
  for (const key of keys1) {
    if (!keys2.includes(key)) return false

    if (
      typeof object1[key] === 'function' ||
      typeof object2[key] === 'function'
    ) {
      if (object1[key].toString() !== object2[key].toString()) return false
    } else if (!isObjectEqual(object1[key], object2[key])) return false
  }
  return true
}
