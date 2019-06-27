import React from 'react'
import styled from 'styled-components'

const Field = styled.input`
  width: 45%;
`
interface Props {
  disabled?: boolean
  defaultValue?: any
  name?: string
  type?: string
}

const FormField = (props: Props) => {
  const { disabled, defaultValue = '' } = props
  return <Field disabled={disabled} defaultValue={defaultValue} {...props} />
}

export default FormField
