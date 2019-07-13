import React from 'react'
import styled from 'styled-components'

const Field = styled.input`
  width: 45%;
`
interface Props {
  disabled?: boolean
  value?: string | number
  onChange?: (e: React.ChangeEvent<any>) => void
  onBlur?: (e: any) => void
  name?: string
  type?: string
}

const FormField = ({ disabled, value, onChange, ...rest }: Props) => (
  <Field disabled={disabled} onChange={onChange} value={value} {...rest} />
)

export default FormField
