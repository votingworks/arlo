import { expect, test } from 'vitest'
import { blankLine, pluralize } from './string'

test('blankLine', () => {
  expect(blankLine(0)).toEqual('')
  expect(blankLine(1)).toEqual('_')
  expect(blankLine(10)).toEqual('__________')
})

test('pluralize', () => {
  expect(pluralize('word', 0)).toEqual('words')
  expect(pluralize('word', 1)).toEqual('word')
  expect(pluralize('word', 2)).toEqual('words')
  expect(pluralize('word', 3)).toEqual('words')
})
