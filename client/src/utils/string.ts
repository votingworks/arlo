// eslint-disable-next-line import/prefer-default-export
export function pluralize(word: string, n: number) {
  return n === 1 ? word : `${word}s`
}
