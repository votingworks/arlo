export function blankLine(length: number): string {
  let line = ''
  for (let i = 0; i < length; i += 1) {
    line += '_'
  }
  return line
}

export function pluralize(word: string, n: number) {
  return n === 1 ? word : `${word}s`
}
