export function isObjectEmpty(object: {}): boolean {
  return Object.keys(object).length === 0
}

export const numberifyObject = (object: {
  [key: string]: string
}): { [key: string]: number } =>
  Object.keys(object).reduce(
    (a, o) => ({
      ...a,
      [o]: Number(object[o].replace(/[^0-9]+/g, '')),
    }),
    {}
  )

export const stringifyObject = (
  object: {
    [key: string]: number
  },
  callback = (s: string) => s
): { [key: string]: string } =>
  Object.keys(object).reduce(
    (a, o) => ({
      ...a,
      [o]: callback(`${object[o]}`),
    }),
    {}
  )

export default isObjectEmpty
