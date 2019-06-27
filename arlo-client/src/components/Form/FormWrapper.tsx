import React from 'react'
import styled from 'styled-components'
import FormTitle from './FormTitle'

const StyledFormWrapper = styled.div`
  display: block;
  width: 50%;
  text-align: left;
`

interface Props {
  title?: string
  children?: any
}

const FormWrapper = (props: Props) => {
  const { title, children } = props
  return (
    <StyledFormWrapper>
      <FormTitle>{title}</FormTitle>
      {children}
    </StyledFormWrapper>
  )
}

export default React.memo(FormWrapper)
