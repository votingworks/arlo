import React from 'react'
import styled from 'styled-components'
import { useAuth0 } from '../react-auth0-spa'
import FormButton from './Form/FormButton'
import {
  Navbar,
  NavbarGroup,
  NavbarHeading,
  Alignment,
} from '@blueprintjs/core'

const ButtonBar = styled.div`
  display: inline-block;
  margin-right: 10px;
`

const Nav = styled(Navbar)`
  width: 100%;

  .bp3-navbar-heading img {
    height: 35px;
    padding-top: 8px;
  }
`

const Header: React.FC<{}> = () => {
  const { isAuthenticated, loginWithRedirect, logout } = useAuth0();
  return (
    <Nav fixedToTop>
      <NavbarGroup align={Alignment.LEFT}>
        <NavbarHeading>
          <img src="/arlo.png" alt="Arlo, by VotingWorks" />
        </NavbarHeading>
      </NavbarGroup>
      <NavbarGroup align={Alignment.RIGHT}>
        <ButtonBar id="reset-button-wrapper" />
        {!isAuthenticated && (
          <FormButton size="sm" onClick={() => loginWithRedirect({})}>Log in</FormButton>
        )}
        {isAuthenticated && <FormButton  size="sm" onClick={() => logout()}>Log out</FormButton>}
      </NavbarGroup>
    </Nav>
  )
}

export default Header
