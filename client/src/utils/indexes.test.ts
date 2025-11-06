import { expect, test } from 'vitest'
import { upTo, formattedUpTo } from './indexes'

test('upTo yields nothing given maximum below 1', () => {
  expect([...upTo(0)]).toEqual([])
})

test('upTo yields 1 given maximum of 1', () => {
  expect([...upTo(1)]).toEqual([1])
})

test('upTo yields values from 1 through the given maximum', () => {
  expect([...upTo(7)]).toEqual([1, 2, 3, 4, 5, 6, 7])
})

test('formattedUpTo yields nothing given maximum below 1', () => {
  expect([...formattedUpTo(0)]).toEqual([])
})

test('formattedUpTo yields 1 given maximum of 1', () => {
  expect([...formattedUpTo(1)]).toEqual(['1'])
})

test('formattedUpTo yields values from 1 through the given maximum', () => {
  expect([...formattedUpTo(7)]).toEqual(['1', '2', '3', '4', '5', '6', '7'])
})

test('formattedUpTo yields values left-padded with zeros so that they are all the same width', () => {
  expect([...formattedUpTo(10)]).toEqual([
    '01',
    '02',
    '03',
    '04',
    '05',
    '06',
    '07',
    '08',
    '09',
    '10',
  ])
})
