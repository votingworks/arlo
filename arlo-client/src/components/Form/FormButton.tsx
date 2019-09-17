import React from 'react'
import { Button } from '@blueprintjs/core'

interface IProps {
  disabled?: boolean
  onClick?: (e: React.FormEvent<any>) => void
  children?: React.ReactNode
  inline?: boolean
  size?: string
  type?: 'button' | 'submit' | 'reset' | undefined
  intent?: 'none' | 'primary' | 'success' | 'warning' | 'danger' | undefined
  fill?: boolean
  loading?: boolean
  large?: boolean
}
const FormButton: React.FC<IProps> = ({
  disabled,
  onClick,
  size,
  inline, // should we use this?
  children,
  ...rest
}: IProps) => (
  <Button onClick={onClick} disabled={disabled} small={size === 'sm'} {...rest}>
    {children}
  </Button>
)

export default FormButton
