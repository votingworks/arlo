import { describe, expect, it, vi } from 'vitest'
import React from 'react'
import { render, fireEvent } from '@testing-library/react'
import FormField, { IProps } from './FormField'

function testForm({
  errors = {},
  touched = {},
  setFieldTouched = vi.fn(),
  setFieldValue = vi.fn(),
}: Partial<IProps['form']> = {}): IProps['form'] {
  return { errors, touched, setFieldTouched, setFieldValue }
}

describe('FormField', () => {
  it('renders a Field', () => {
    const field = {
      name: 'field-name',
      value: 'text value',
      onChange: vi.fn(),
      onBlur: vi.fn(),
    }
    const form = testForm()
    const { container } = render(
      <FormField field={field} form={form} type="text" />
    )

    expect(container).toMatchSnapshot()
  })

  it('renders a numeric Field', () => {
    const field = {
      name: 'field-name',
      value: 'text value',
      onChange: vi.fn(),
      onBlur: vi.fn(),
    }
    const form = testForm()
    const { container, getByTestId } = render(
      <FormField field={field} form={form} type="number" data-testid="testid" />
    )

    expect(container).toMatchSnapshot()

    const input = getByTestId('testid')
    fireEvent.change(input, { target: { value: 'new value' } })
    fireEvent.blur(input)

    expect(field.onChange).toBeCalledTimes(0)
    expect(form.setFieldTouched).toBeCalledTimes(1)
    expect(form.setFieldValue).toBeCalledTimes(1)
  })

  it('renders a Field with errors', () => {
    const field = {
      name: 'field-name',
      value: '',
      onChange: vi.fn(),
      onBlur: vi.fn(),
    }
    const form = testForm({
      errors: {
        'field-name': 'Required',
      },
      touched: {
        'field-name': true,
      },
    })
    const { container } = render(
      <FormField field={field} form={form} type="text" />
    )

    expect(container).toMatchSnapshot()
  })

  it('calls onChange', () => {
    const field = {
      name: 'field-name',
      value: '',
      onChange: vi.fn(),
      onBlur: vi.fn(),
    }
    const form = testForm()
    const { getByTestId } = render(
      <FormField field={field} form={form} type="text" data-testid="testid" />
    )

    fireEvent.change(getByTestId('testid'), { target: { value: 'new value' } })

    expect(field.onChange).toBeCalledTimes(1)
  })
})
