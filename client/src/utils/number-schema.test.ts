import { describe, expect, it } from 'vitest'
import number, { parse, RoundMethod } from './number-schema'

describe('parse', () => {
  it('returns NaN given empty string', () => {
    expect(parse('')).toBe(NaN)
  })

  it('returns numbers as-is', () => {
    expect(parse(0)).toBe(0)
    expect(parse(1000)).toBe(1000)
    expect(parse(10.1)).toBe(10.1)
  })

  it('returns value of Number instances', () => {
    // eslint-disable-next-line no-new-wrappers
    expect(parse(new Number(1))).toBe(1)
  })

  it('parses strings without grouping separators', () => {
    expect(parse('1234')).toBe(1234)
    expect(parse('1234.56')).toBe(1234.56)
  })

  it('parses strings with grouping separators', () => {
    expect(parse('1,234')).toBe(1234)
    expect(parse('1,234,567')).toBe(1234567)
  })

  it('returns NaN for anything it cannot handle', () => {
    expect(parse('123abc')).toBe(NaN)
    expect(parse({})).toBe(NaN)
  })
})

describe('NumberSchema', () => {
  it('can be used as a basic number validator', async () => {
    expect(await number().validate(1)).toBe(1)
  })

  it('can be used to enforce that a number is required', async () => {
    await expect(
      number()
        .required()
        .validate(undefined)
    ).rejects.toThrowError()
  })

  it('can type check a value', () => {
    expect(number().isType(1)).toBe(true)
    // eslint-disable-next-line no-new-wrappers
    expect(number().isType(new Number(1))).toBe(true)
    expect(number().isType(NaN)).toBe(false)
    expect(number().isType('foo')).toBe(false)
  })

  it('can enforce a number is less than something', async () => {
    expect(
      await number()
        .lessThan(5)
        .validate(4)
    ).toBe(4)
    await expect(
      number()
        .lessThan(5, 'too high')
        .validate(6)
    ).rejects.toThrowError('too high')
  })

  it('can enforce a number is more than something', async () => {
    expect(
      await number()
        .moreThan(5)
        .validate(6)
    ).toBe(6)
    await expect(
      number()
        .moreThan(5, 'too low')
        .validate(4)
    ).rejects.toThrowError('too low')
  })

  it('can enforce a maximum', async () => {
    expect(
      await number()
        .max(5)
        .validate(4)
    ).toBe(4)
    await expect(
      number()
        .max(3)
        .validate(4)
    ).rejects.toThrowError()
  })

  it('can enforce a minimum', async () => {
    expect(
      await number()
        .min(4)
        .validate(5)
    ).toBe(5)
    await expect(
      number()
        .min(4)
        .validate(3)
    ).rejects.toThrowError()
  })

  it('can enforce positive numbers', async () => {
    expect(
      await number()
        .positive()
        .validate(1)
    ).toBe(1)
    await expect(
      number()
        .positive('must be positive')
        .validate(0)
    ).rejects.toThrowError('must be positive')
    await expect(
      number()
        .positive('must be positive')
        .validate(-1)
    ).rejects.toThrowError('must be positive')
  })

  it('can enforce negative numbers', async () => {
    expect(
      await number()
        .negative()
        .validate(-1)
    ).toBe(-1)
    await expect(
      number()
        .negative('must be negative')
        .validate(0)
    ).rejects.toThrowError('must be negative')
    await expect(
      number()
        .negative('must be negative')
        .validate(1)
    ).rejects.toThrowError('must be negative')
  })

  it('can enforce integer values', async () => {
    expect(
      await number()
        .integer()
        .validate(1)
    ).toBe(1)
    await expect(
      number()
        .integer()
        .validate(1.1)
    ).rejects.toThrowError()
  })

  it('can truncate numbers', async () => {
    expect(
      await number()
        .truncate()
        .validate(1.1)
    ).toBe(1)
    expect(
      await number()
        .truncate()
        .validate(undefined)
    ).toBe(undefined)
  })

  it.each<[RoundMethod, number, number]>([
    ['ceil', 1.1, 2],
    ['floor', 1.1, 1],
    ['floor', -1.1, -2],
    ['round', 1.1, 1],
    ['round', 1.5, 2],
    ['trunc', 1.1, 1],
    ['trunc', -1.1, -1],
  ])('can round with mode "%s" %d -> %d', async (mode, input, output) => {
    expect(
      await number()
        .round(mode)
        .validate(input)
    ).toBe(output)
  })

  it('passes missing values through rounding', async () => {
    expect(
      await number()
        .round()
        .validate(undefined)
    ).toBe(undefined)
  })

  it('defaults to "round" mode', async () => {
    expect(
      await number()
        .round()
        .validate(1.5)
    ).toBe(2)
  })

  it('allows capitalized round modes', async () => {
    expect(
      await number()
        .round('TRUNC' as RoundMethod)
        .validate(-1.1)
    ).toBe(-1)
  })

  it('fails on an invalid round mode', () => {
    expect(() =>
      number()
        .round('invalid' as RoundMethod)
        .validate(0)
    ).toThrowError()
  })
})
