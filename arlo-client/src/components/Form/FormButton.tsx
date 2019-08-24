import React from 'react'
import { Button } from '@blueprintjs/core'

interface Props {
  disabled?: boolean
  onClick?: (e: React.FormEvent<any>) => void
  children?: React.ReactNode
  inline?: boolean
  size?: string
  type?: 'button' | 'submit' | 'reset' | undefined
  intent?: 'none' | 'primary' | 'success' | 'warning' | 'danger' | undefined
}
const FormButton: React.FC<Props> = ({
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
