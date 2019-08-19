import React from 'react'
import { Button } from '@blueprintjs/core'

interface Props {
  disabled?: boolean
  onClick?: any
  children?: any
  inline?: boolean
  size?: string
  type?: 'button' | 'submit' | 'reset' | undefined
  intent?: 'none' | 'primary' | 'success' | 'warning' | 'danger' | undefined
}
const FormButton = ({
  disabled,
  onClick,
  size,
  inline, // should we use this?
  children,
  ...rest
}: Props) => (
  <Button onClick={onClick} disabled={disabled} small={size === 'sm'} {...rest}>
    {children}
  </Button>
)

export default FormButton
