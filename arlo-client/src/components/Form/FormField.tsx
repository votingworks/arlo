import React from 'react'
import styled from 'styled-components'
import { getIn, FieldProps } from 'formik'

const Wrapper = styled.div`
  width: 45%;
`

const Field = styled.input`
  width: 100%;
`

const ErrorLabel = styled.p`
  width: 100%;
  color: #ff0000;
  font-size: 10px;
`

interface Props {
  field: FieldProps['field']
  form: FieldProps['form']
  disabled?: boolean
  value?: string | number
  onChange?: (e: React.ChangeEvent) => void
  onBlur?: (e: React.FocusEvent) => void
  name?: string
  type?: string
  error?: string
  touched?: boolean
  className?: string
}

const FormField: React.FC<Props> = ({
  field,
  form: { touched, errors },
  disabled,
  className,
  ...rest
}: Props) => (
  <Wrapper className={className}>
    <Field disabled={disabled} {...field} {...rest} />
    {getIn(errors, field.name) && getIn(touched, field.name) && (
      <ErrorLabel data-testid={`${field.name}-error`}>
        {getIn(errors, field.name)}
      </ErrorLabel>
    )}
  </Wrapper>
)

export default FormField
