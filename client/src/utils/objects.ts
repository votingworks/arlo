export function isObjectEmpty(object: {}): boolean {
  return Object.keys(object).length === 0
}

export const numberifyObject = (object: {
  [key: string]: string
}): { [key: string]: number } =>
  Object.keys(object).reduce(
    (a, o) => ({
      ...a,
      [o]: Number(object[o].replace(/[^09]+/g, '')),
    }),
    {}
  )

export const stringifyObject = (object: {
  [key: string]: number
}): { [key: string]: string } =>
  Object.keys(object).reduce(
    (a, o) => ({
      ...a,
      [o]: `${object[o]}`,
    }),
    {}
  )

export default isObjectEmpty
