import React from 'react'
import styled from 'styled-components'

const HeaderContainer = styled.div`
  width: 100%;
  padding: 20px;
  text-align: center;
`
const ButtonBar = styled.div`
  display: inline-block;
  float: right;
`

const Header = () => {
  return (
    <HeaderContainer>
      <img height="60px" src="/arlo.png" alt="Arlo, by VotingWorks" />
      <ButtonBar id="reset-button-wrapper" />
    </HeaderContainer>
  )
}

export default Header
