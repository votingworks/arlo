import React, { ReactNode } from 'react'
import styled from 'styled-components'
import H2Title from '../H2Title'

const StyledFormWrapper = styled.div`
  display: block;
  position: relative;
  max-width: 30rem;
  text-align: left;
`

interface IProps {
  title?: string
  children?: ReactNode
}

const FormWrapper: React.FC<IProps> = ({
  children,
  title,
}: IProps): React.ReactElement => (
  <StyledFormWrapper>
    <H2Title>{title}</H2Title>
    {children}
  </StyledFormWrapper>
)

export default React.memo(FormWrapper)
