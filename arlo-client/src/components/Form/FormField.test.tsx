import React from 'react'
import { render, fireEvent } from '@testing-library/react'
import { FormikProps } from 'formik'
import FormField from './FormField'

describe('FormField', () => {
  it('renders a Field', () => {
    const field = {
      name: 'field-name',
      value: 'text value',
      onChange: jest.fn(),
      onBlur: jest.fn(),
    }
    const form = ({
      errors: {},
      touched: {},
    } as any) as FormikProps<any> // eslint-disable-line @typescript-eslint/no-object-literal-type-assertion
    const { container } = render(
      <FormField field={field} form={form} type="text" />
    )

    expect(container).toMatchSnapshot()
  })

  it('renders a numeric Field', () => {
    const field = {
      name: 'field-name',
      value: 'text value',
      onChange: jest.fn(),
      onBlur: jest.fn(),
    }
    const form = ({
      errors: {},
      touched: {},
      setFieldTouched: jest.fn(),
      setFieldValue: jest.fn(),
    } as any) as FormikProps<any> // eslint-disable-line @typescript-eslint/no-object-literal-type-assertion
    const { container, getByTestId } = render(
      <FormField field={field} form={form} type="number" data-testid="testid" />
    )

    expect(container).toMatchSnapshot()

    const input = getByTestId('testid')
    fireEvent.change(input, { target: { value: 'new value' } })
    fireEvent.blur(input)

    expect(field.onChange).toHaveBeenCalledTimes(0)
    expect(form.setFieldTouched).toHaveBeenCalledTimes(1)
    expect(form.setFieldValue).toHaveBeenCalledTimes(1)
  })

  it('renders a Field with errors', () => {
    const field = {
      name: 'field-name',
      value: '',
      onChange: jest.fn(),
      onBlur: jest.fn(),
    }
    const form = ({
      errors: {
        'field-name': 'Required',
      },
      touched: {
        'field-name': true,
      },
    } as any) as FormikProps<any> // eslint-disable-line @typescript-eslint/no-object-literal-type-assertion
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
    const form = ({
      errors: {},
      touched: {},
    } as any) as FormikProps<any>
    const { getByTestId } = render(
      <FormField field={field} form={form} type="text" data-testid="testid" />
    )

    fireEvent.change(getByTestId('testid'), { target: { value: 'new value' } })

    expect(field.onChange).toBeCalledTimes(1)
  })
})
