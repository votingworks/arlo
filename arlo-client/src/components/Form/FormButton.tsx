import React from 'react'
import { Button } from '@blueprintjs/core'
import styled from 'styled-components'

const SpacedButton = styled(Button)`
  & + & {
    margin-top: 10px;
  }
`

interface Props {
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
const FormButton: React.FC<Props> = ({
  disabled,
  onClick,
  size,
  inline, // should we use this?
  children,
  ...rest
}: Props) => (
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
