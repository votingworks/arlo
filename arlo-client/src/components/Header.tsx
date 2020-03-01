import React, { useContext } from 'react'
import styled from 'styled-components'
import {
  Navbar,
  NavbarGroup,
  NavbarHeading,
  Alignment,
} from '@blueprintjs/core'
import { Route, Link } from 'react-router-dom'
import { useAuth0, IAuth0Context } from '../react-auth0-spa'
import FormButton from './Form/FormButton'
import UserContext from '../UserContext'
import { ICreateAuditParams } from '../types'

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

interface IProps {
  match: {
    params: ICreateAuditParams
  }
}

const Header: React.FC<IProps> = ({
  match: {
    params: { electionId },
  },
}: IProps) => {
  const {
    isAuthenticated,
    loginWithRedirect,
    logout,
  } = useAuth0() as IAuth0Context
  const user = useContext(UserContext)
  return (
    <Nav fixedToTop>
      <NavbarGroup align={Alignment.LEFT}>
        <NavbarHeading>
          <img src="/arlo.png" alt="Arlo, by VotingWorks" />
        </NavbarHeading>
      </NavbarGroup>
      <NavbarGroup align={Alignment.RIGHT}>
        <ButtonBar id="reset-button-wrapper" />
        <Route
          path="/election"
          render={() =>
            !isAuthenticated && (
              <FormButton size="sm" onClick={() => loginWithRedirect({})}>
                Log in
              </FormButton>
            )
          }
        />
        {isAuthenticated && (
          <FormButton size="sm" onClick={() => logout()}>
            Log out
          </FormButton>
        )}
      </NavbarGroup>
      {isAuthenticated && (
        <>
          <NavbarGroup align={Alignment.LEFT}>
            <NavbarHeading>Welcome, {user.name}</NavbarHeading>
          </NavbarGroup>
          {user.permissions['create:audits'] && (
            <NavbarGroup align={Alignment.RIGHT}>
              <NavbarHeading>
                <Link to="/">New Audit</Link>
              </NavbarHeading>
            </NavbarGroup>
          )}
          {user.permissions['manage:audits'] && (
            <NavbarGroup align={Alignment.RIGHT}>
              <NavbarHeading>
                <Link to="/">View Audits</Link>
              </NavbarHeading>
            </NavbarGroup>
          )}
          {user.permissions['manage:audits'] && electionId && (
            <NavbarGroup align={Alignment.RIGHT}>
              <NavbarHeading>
                <Link to={`/election/${electionId}`}>Audit Progress</Link>
              </NavbarHeading>
            </NavbarGroup>
          )}
          {user.permissions['create:audits'] && electionId && (
            <NavbarGroup align={Alignment.RIGHT}>
              <NavbarHeading>
                <Link to={`/election/${electionId}/setup`}>Audit Setup</Link>
              </NavbarHeading>
            </NavbarGroup>
          )}
        </>
      )}
    </Nav>
  )
}

export default Header
