import React from 'react'
import styled from 'styled-components'
import {
  Navbar,
  NavbarGroup,
  NavbarHeading,
  Alignment,
  NavbarDivider,
} from '@blueprintjs/core'
import { Link, useRouteMatch, RouteComponentProps } from 'react-router-dom'
import { useAuthDataContext } from './UserContext'
import FormButton from './Atoms/Form/FormButton'

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

  .bp3-navbar-divider {
    margin-right: 15px;
    margin-left: 0;
  }
`

interface TParams {
  electionId: string
}

const Header: React.FC<{}> = () => {
  const match: RouteComponentProps<TParams>['match'] | null = useRouteMatch(
    '/election/:electionId'
  )
  const electionId = match ? match.params.electionId : undefined
  const { isAuthenticated, meta } = useAuthDataContext()
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
        {isAuthenticated && electionId && meta!.type === 'audit_admin' && (
          <>
            <NavbarHeading>
              <Link to={`/election/${electionId}/setup`}>Audit Setup</Link>
            </NavbarHeading>
            <NavbarDivider />
            <NavbarHeading>
              <Link to={`/election/${electionId}/progress`}>
                Audit Progress
              </Link>
            </NavbarHeading>
            <NavbarDivider />
            <NavbarHeading>
              <Link to="/">View Audits</Link>
            </NavbarHeading>
            <NavbarDivider />
            <NavbarHeading>
              <Link to="/">New Audit</Link>
            </NavbarHeading>
          </>
        )}
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
