import React from 'react'
import { Button } from '@blueprintjs/core'
import styled from 'styled-components'

const VerticalSpacedButton = styled(Button)`
  & + & {
    margin-top: 10px;
  }
`
const HorizontalSpacedButton = styled(Button)`
  & + & {
    margin-left: 10px;
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
  verticalSpaced?: boolean
  minimal?: boolean
}
const FormButton = ({
  disabled,
  onClick,
  size,
  children,
  verticalSpaced,
  ...rest
}: IProps): React.ReactElement =>
  verticalSpaced ? (
    <VerticalSpacedButton
      onClick={onClick}
      disabled={disabled}
      small={size === 'sm'}
      {...rest}
    >
      {children}
    </VerticalSpacedButton>
  ) : (
    <HorizontalSpacedButton
      onClick={onClick}
      disabled={disabled}
      small={size === 'sm'}
      {...rest}
    >
      {children}
    </HorizontalSpacedButton>
  )

export default FormButton
