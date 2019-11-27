import React from 'react'
import { Button } from '@blueprintjs/core'
import styled from 'styled-components'

const SpacedButton = styled(Button)`
  & + & {
    margin-top: 10px;
  }
`

interface IProps {
  disabled?: boolean
  onClick?: (e: React.FormEvent<any>) => void // eslint-disable-line @typescript-eslint/no-explicit-any
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
  // should we use this?
  inline, // eslint-disable-line @typescript-eslint/no-unused-vars
  children,
  ...rest
}: IProps) => (
  <SpacedButton
    onClick={onClick}
    disabled={disabled}
    small={size === 'sm'}
    {...rest}
  >
    {children}
  </SpacedButton>
)

export default FormButton
