import React from 'react'
import styled from 'styled-components'
import {
  Navbar,
  NavbarGroup,
  NavbarHeading,
  Alignment,
  NavbarDivider,
  Tag,
  Button,
  Menu,
  MenuItem,
  Popover,
  Position,
  Colors,
} from '@blueprintjs/core'
import { Link, useRouteMatch, RouteComponentProps } from 'react-router-dom'
import { useAuthDataContext } from './UserContext'
import FormButton from './Atoms/Form/FormButton'
import { Inner } from './Atoms/Wrapper'
import LinkButton from './Atoms/LinkButton'

const SupportBar = styled(Navbar)`
  background-color: ${Colors.ORANGE5};
  height: 30px;
  padding: 0;
  .bp3-navbar-group {
    height: 30px;
  }
`

const Nav = styled(Navbar)`
  width: 100%;
  padding: 0;

  .bp3-navbar-heading img {
    height: 35px;
    padding-top: 5px;
  }
`

const UserMenu = styled.div`
  .bp3-button {
    width: 200px;
  }
  .bp3-button-text {
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .bp3-menu {
    width: 200px;
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
    <>
      {auth && auth.superadminUser && (
        <SupportBar>
          <InnerBar>
            <NavbarGroup align={Alignment.LEFT}>
              <NavbarHeading>Support Tools</NavbarHeading>
            </NavbarGroup>
            <NavbarGroup align={Alignment.RIGHT}>
              <NavbarHeading>{auth.superadminUser.email}</NavbarHeading>
            </NavbarGroup>
          </InnerBar>
        </SupportBar>
      )}
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
          {auth && auth.user && (
            <NavbarGroup align={Alignment.RIGHT}>
              {electionId && auth.user.type === 'audit_admin' && (
                <>
                  <LinkButton
                    to={`/election/${electionId}/setup`}
                    minimal
                    icon="wrench"
                  >
                    Audit Setup
                  </LinkButton>
                  <LinkButton
                    to={`/election/${electionId}/progress`}
                    minimal
                    icon="horizontal-bar-chart"
                  >
                    Audit Progress
                  </LinkButton>
                  <LinkButton to="/" minimal icon="projects">
                    View Audits
                  </LinkButton>
                  <LinkButton to="/" minimal icon="insert">
                    New Audit
                  </LinkButton>
                  <NavbarDivider />
                </>
              )}
              {auth.user.type !== 'audit_board' && (
                <UserMenu>
                  <Popover
                    content={
                      <Menu>
                        <MenuItem
                          text="Log out"
                          onClick={() =>
                            window.location.replace('/auth/logout')
                          }
                        />
                      </Menu>
                    }
                    usePortal={false}
                    position={Position.BOTTOM}
                    minimal
                    fill
                  >
                    <Button icon="user" minimal>
                      {auth.user.email}
                    </Button>
                  </Popover>
                </UserMenu>
              )}
            </NavbarGroup>
          )}
        </InnerBar>
      </Nav>
    </>
  )
}

export default Header
