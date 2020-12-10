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
import { Inner } from './Atoms/Wrapper'

const ButtonBar = styled.div`
  display: inline-block;
  margin-right: 10px;
`

const Nav = styled(Navbar)`
  width: 100%;
  padding: 0;

  .bp3-navbar-heading img {
    height: 35px;
    padding-top: 5px;
  }

  .bp3-navbar-divider {
    margin-right: 15px;
    margin-left: 0;
  }
`

const InnerBar = styled(Inner)`
  display: inherit;
`

interface TParams {
  electionId: string
  jurisdictionId?: string
}

const Header: React.FC<{}> = () => {
  const electionMatch:
    | RouteComponentProps<TParams>['match']
    | null = useRouteMatch('/election/:electionId')
  const jurisdictionMatch:
    | RouteComponentProps<TParams>['match']
    | null = useRouteMatch(
    '/election/:electionId/jurisdiction/:jurisdictionId?'
  )
  const auth = useAuthDataContext()
  const electionId = electionMatch ? electionMatch.params.electionId : undefined
  const jurisdiction =
    jurisdictionMatch &&
    auth &&
    auth.user &&
    auth.user.type === 'jurisdiction_admin' &&
    auth.user.jurisdictions.find(
      j => j.id === jurisdictionMatch.params.jurisdictionId
    )
  return (
    <Nav>
      <InnerBar>
        <NavbarGroup align={Alignment.LEFT}>
          <NavbarHeading>
            <Link to="/">
              <img src="/arlo.png" alt="Arlo, by VotingWorks" />
            </Link>
          </NavbarHeading>
          {jurisdiction && (
            <NavbarHeading>Jurisdiction: {jurisdiction.name}</NavbarHeading>
          )}
        </NavbarGroup>
        <NavbarGroup align={Alignment.RIGHT}>
          {electionId && auth && auth.user && auth.user.type === 'audit_admin' && (
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
          auth && auth.user && (
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
      </InnerBar>
    </Nav>
  )
}

export default Header
