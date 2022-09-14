import React from 'react'
import styled from 'styled-components'
import { InputGroup, NumericInput, TextArea } from '@blueprintjs/core'
import { getIn, FieldProps } from 'formik'
import { ErrorLabel } from './_helpers'

interface IWrapperProps {
  wide: boolean
}

const Wrapper = styled.div<IWrapperProps>`
  width: ${p => (p.wide ? '100%' : '45%')};
`

const Field = styled(InputGroup)`
  margin-top: 5px;
  width: 100%;
`

const Area = styled(TextArea)`
  margin-top: 5px;
  width: 100%;
`

const NumberField = styled(NumericInput)`
  margin-top: 5px;
  width: 100%;
  .bp3-input-group {
    width: 100%;
  }
  input.bp3-input {
    margin-top: 0;
  }
  .bp3-button-group.bp3-vertical.bp3-fixed {
    transform: translateX(-100%);
    z-index: 15;
  }
`

export interface IProps {
  field: FieldProps['field']
  form: Pick<
    FieldProps['form'],
    'touched' | 'errors' | 'setFieldTouched' | 'setFieldValue'
  >
  disabled?: boolean
  value?: string | number
  onChange?: (e: React.FormEvent) => void
  onBlur?: (e: React.FocusEvent) => void
  name?: string
  type?: string
  error?: string
  touched?: boolean
  className?: string
}

const FormField: React.FC<IProps> = ({
  field,
  form: { touched, errors, setFieldTouched, setFieldValue },
  disabled,
  className,
  type,
  ...rest
}: IProps) => (
  <Wrapper className={className} wide={type === 'textarea'}>
    {type === 'number' ? (
      <NumberField
        disabled={disabled}
        onValueChange={n => setFieldValue(field.name, n)}
        type={type}
        {...field}
        {...rest}
        onBlur={() => setFieldTouched(field.name)}
      />
    ) : type === 'textarea' ? (
      <Area disabled={disabled} {...field} {...rest} />
    ) : (
      <Field disabled={disabled} type={type} {...field} {...rest} />
    )}
    {getIn(errors, field.name) && getIn(touched, field.name) && (
      <ErrorLabel data-testid={`${field.name}-error`}>
        {getIn(errors, field.name)}
      </ErrorLabel>
    )}
  </Wrapper>
)

export default FormField
