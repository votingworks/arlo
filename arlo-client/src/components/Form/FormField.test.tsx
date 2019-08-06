import React from 'react'
import { render, fireEvent } from '@testing-library/react'
import FormField from './FormField'

describe('FormField', () => {
  it('renders a Field', () => {
    const field = {
      name: 'field-name',
      value: 'text value',
      onChange: jest.fn(),
      onBlur: jest.fn(),
    }
    const form = {
      errors: {},
      touched: {},
    }
    const { container } = render(
      <FormField field={field} form={form} type="text" />
    )

    expect(container).toMatchSnapshot()
  })

  it('renders a Field with errors', () => {
    const field = {
      name: 'field-name',
      value: '',
      onChange: jest.fn(),
      onBlur: jest.fn(),
    }
    const form = {
      errors: {
        'field-name': 'Required',
      },
      touched: {
        'field-name': true,
      },
    }
    const { container } = render(
      <FormField field={field} form={form} type="text" />
    )

    expect(container).toMatchSnapshot()
  })

  it('calls onChange', () => {
    const field = {
      name: 'field-name',
      value: '',
      onChange: jest.fn(),
      onBlur: jest.fn(),
    }
    const form = {
      errors: {},
      touched: {},
    }
    const { getByTestId } = render(
      <FormField field={field} form={form} type="text" data-testid="testid" />
    )

    fireEvent.change(getByTestId('testid'), { target: { value: 'new value' } })

    expect(field.onChange).toHaveBeenCalledTimes(1)
  })
})
