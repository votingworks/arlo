/* eslint-disable @typescript-eslint/ban-ts-comment */
/**
 * This file was mostly copy-pasted from https://github.com/jquense/yup/blob/1426feceb6c5544c526711bedcf388afaf6115b9/src/number.js.
 *
 * It has been modified to support parsing numbers with grouping separators,
 * i.e. `1,234`. Unfortunately, Yup doesn't seem to have a way to subclass its
 * `NumberSchema` to customize this behavior, so we have to just define our own.
 */

import * as Yup from 'yup'

// @ts-ignore
import MixedSchema from 'yup/lib/mixed'

// @ts-ignore
import { number as locale } from 'yup/lib/locale'

// @ts-ignore
import isAbsent from 'yup/lib/util/isAbsent'

export type RoundMethod = 'ceil' | 'floor' | 'round' | 'trunc'

function getGroupingSeparator() {
  const formatter = new Intl.NumberFormat(undefined, {
    useGrouping: true,
  })

  // Use a big enough number to have a grouping separator.
  for (const { type, value } of formatter.formatToParts(1000)) {
    if (type === 'group') {
      return value
    }
  }

  // Use a default if for some reason there is none.
  /* istanbul ignore next */
  return ','
}

const GroupingSeparator = getGroupingSeparator()

export function parse(value: unknown): number {
  if (typeof value === 'number') {
    return value
  }

  if (typeof value === 'string') {
    const normalized = value
      .replace(/\s/g, '')
      .replace(new RegExp(`\\${GroupingSeparator}`, 'g'), '')

    if (normalized === '') return NaN

    // don't use parseFloat to avoid false positives on alpha-numeric strings
    return +normalized
  }

  if (value instanceof Number) {
    return value.valueOf()
  }

  return NaN
}

export class NumberSchema extends (MixedSchema as new (
  ...args: unknown[]
) => Yup.MixedSchema) {
  public constructor() {
    // eslint-disable-next-line constructor-super
    super({ type: 'number' })

    this.withMutation(() => {
      this.transform(parse)
    })
  }

  protected _typeCheck(possiblyWrappedValue: unknown): boolean {
    const value =
      possiblyWrappedValue instanceof Number
        ? possiblyWrappedValue.valueOf()
        : possiblyWrappedValue

    return typeof value === 'number' && !Number.isNaN(value)
  }

  public min(min: number, message = locale.min): this {
    return this.test({
      message,
      name: 'min',
      exclusive: true,
      params: { min },
      test(value) {
        return isAbsent(value) || value >= this.resolve(min)
      },
    })
  }

  public max(max: number, message = locale.max): this {
    return this.test({
      message,
      name: 'max',
      exclusive: true,
      params: { max },
      test(value) {
        return isAbsent(value) || value <= this.resolve(max)
      },
    })
  }

  public lessThan(less: number, message = locale.lessThan): this {
    return this.test({
      message,
      name: 'max',
      exclusive: true,
      params: { less },
      test(value) {
        return isAbsent(value) || value < this.resolve(less)
      },
    })
  }

  public moreThan(more: number, message = locale.moreThan): this {
    return this.test({
      message,
      name: 'min',
      exclusive: true,
      params: { more },
      test(value) {
        return isAbsent(value) || value > this.resolve(more)
      },
    })
  }

  public positive(msg = locale.positive): this {
    return this.moreThan(0, msg)
  }

  public negative(msg = locale.negative): this {
    return this.lessThan(0, msg)
  }

  public integer(message = locale.integer): this {
    return this.test({
      name: 'integer',
      message,
      test: val => isAbsent(val) || Number.isInteger(val),
    })
  }

  public truncate(): this {
    /* istanbul ignore next */
    // eslint-disable-next-line no-bitwise
    return this.transform(value => (!isAbsent(value) ? value | 0 : value))
  }

  public round(methodWithPossibleIncorrectCasing?: RoundMethod): this {
    const avail = ['ceil', 'floor', 'round', 'trunc']
    const method =
      (methodWithPossibleIncorrectCasing &&
        (methodWithPossibleIncorrectCasing.toLowerCase() as RoundMethod)) ||
      'round'

    // this exists for symemtry with the new Math.trunc
    if (method === 'trunc') return this.truncate()

    if (avail.indexOf(method.toLowerCase()) === -1)
      throw new TypeError(
        `Only valid options for round() are: ${avail.join(', ')}`
      )

    return this.transform(value =>
      /* istanbul ignore next */
      !isAbsent(value) ? Math[method!](value) : value
    )
  }
}

export default function number(): NumberSchema {
  return new NumberSchema()
}
