import React from 'react'
import styled from 'styled-components'
import {
  Navbar,
  NavbarGroup,
  NavbarHeading,
  Alignment,
} from '@blueprintjs/core'
import { Link } from 'react-router-dom'
import { useAuthDataContext } from './UserContext'
import FormButton from './Form/FormButton'

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
  const { isAuthenticated } = useAuthDataContext()
  return (
    <Nav fixedToTop>
      <NavbarGroup align={Alignment.LEFT}>
        <NavbarHeading>
          <Link to="/">
            <img src="/arlo.png" alt="Arlo, by VotingWorks" />
          </Link>
        </NavbarHeading>
      </NavbarGroup>
      <NavbarGroup align={Alignment.RIGHT}>
        <ButtonBar id="reset-button-wrapper" />
        {/* istanbul ignore next */
        isAuthenticated && (
          <FormButton
            size="sm"
            onClick={
              /* istanbul ignore next */
              () => window.location.replace('/auth/logout')
            }
          >
            Log out
          </FormButton>
        )}
      </NavbarGroup>
    </Nav>
  )
}

export default Header
