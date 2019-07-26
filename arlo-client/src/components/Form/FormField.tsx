import React from 'react'
import styled from 'styled-components'

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
  field?: any
  form?: any
  disabled?: boolean
  value?: string | number
  onChange?: (e: React.ChangeEvent<any>) => void
  onBlur?: (e: any) => void
  name?: string
  type?: string
  error?: string
  touched?: boolean
  className?: string
}

const FormField = ({
  field,
  form: { touched, errors },
  disabled,
  className,
  ...rest
}: Props) => (
  <Wrapper className={className}>
    <Field disabled={disabled} {...field} {...rest} />
    {errors[field.name] && touched[field.name] && (
      <ErrorLabel>{errors[field.name]}</ErrorLabel>
    )}
  </Wrapper>
)

export default FormField
