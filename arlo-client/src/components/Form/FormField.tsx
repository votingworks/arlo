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
  disabled,
  value,
  error,
  touched,
  onChange,
  className,
  ...rest
}: Props) => (
  <Wrapper className={className}>
    <Field disabled={disabled} onChange={onChange} value={value} {...rest} />
    {error && touched && <ErrorLabel>{error}</ErrorLabel>}
  </Wrapper>
)

export default FormField
