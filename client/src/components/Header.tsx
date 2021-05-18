import React from 'react'
import styled from 'styled-components'
import {
  Navbar,
  NavbarGroup,
  NavbarHeading,
  Alignment,
  NavbarDivider,
  Button,
  Menu,
  MenuItem,
  Popover,
  Position,
  Colors,
  Icon,
} from '@blueprintjs/core'
import { Link, useRouteMatch, RouteComponentProps } from 'react-router-dom'
import { useAuthDataContext } from './UserContext'
import { Inner } from './Atoms/Wrapper'
import LinkButton from './Atoms/LinkButton'

const SupportBar = styled(Navbar)`
  background-color: ${Colors.ROSE3};
  height: 35px;
  padding: 0;
  color: ${Colors.WHITE};
  font-weight: 500;

  .bp3-navbar-group {
    height: 35px;
  }

  a {
    text-decoration: none;
    color: ${Colors.WHITE};
    .bp3-icon {
      margin-right: 8px;
    }
  }

  .bp3-navbar-divider {
    border-color: rgba(255, 255, 255, 0.7);
  }
`

const Nav = styled(Navbar)`
  width: 100%;
  height: auto;
  padding: 0;

  .bp3-navbar-heading img {
    height: 35px;
    padding-top: 5px;
  }
`

const AuditBoardNav = styled(Navbar)`
  background-color: #000000;
  width: 100%;
  height: auto;
  padding: 0;
  color: #ffffff;
  .bp3-navbar-heading img {
    height: 35px;
    padding-top: 5px;
  }
`

const UserMenu = styled.div`
  .bp3-button {
    border: 1px solid ${Colors.GRAY4};
    width: 200px;
  }
  .bp3-button-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .bp3-menu {
    width: 200px;
  }
`

const InnerBar = styled(Inner)`
  display: inherit;
`

const AuditBoardInnerBar = styled(Inner)`
  justify-content: space-between;
  .members-name {
    margin-bottom: 0;
  }
`

const NavbarGroupAuditBoardLink = styled(NavbarGroup)`
  a {
    color: #ffffff;
  }
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
  const supportMatch = useRouteMatch('/support')
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
      {auth && auth.supportUser && (
        <SupportBar>
          <InnerBar>
            <NavbarGroup align={Alignment.LEFT}>
              <a href="/support">
                <Icon icon="eye-open" />
                <span>Arlo Support Tools</span>
              </a>
            </NavbarGroup>
            <NavbarGroup align={Alignment.RIGHT}>
              <span>{auth.supportUser.email}</span>
              <NavbarDivider />
              <a href="/auth/support/logout">Log out</a>
            </NavbarGroup>
          </InnerBar>
        </SupportBar>
      )}
      {!supportMatch && auth && auth.user && auth.user.type !== 'audit_board' && (
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
                <UserMenu>
                  <Popover
                    content={
                      <Menu>
                        <MenuItem text="Log out" href="/auth/logout" />
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
              </NavbarGroup>
            )}
          </InnerBar>
        </Nav>
      )}
      {auth && auth.user && auth.user.type === 'audit_board' && (
        <AuditBoardNav>
          <AuditBoardInnerBar>
            <NavbarGroup>
              <NavbarHeading>
                <Link to="/">
                  <img src="/arlo.png" alt="Arlo, by VotingWorks" />
                </Link>
              </NavbarHeading>
            </NavbarGroup>
            <NavbarGroup>
              <p className="members-name">
                {auth.user.name} :{' '}
                <strong>
                  {auth.user.members.map(member => member.name).join(', ')}
                </strong>
              </p>
            </NavbarGroup>
            <NavbarGroupAuditBoardLink>
              <Link to="/auth/logout">Sign Out</Link>
            </NavbarGroupAuditBoardLink>
          </AuditBoardInnerBar>
        </AuditBoardNav>
      )}
      {!supportMatch && !auth && (
        <Nav>
          <InnerBar>
            <NavbarGroup align={Alignment.LEFT}>
              <NavbarHeading>
                <Link to="/">
                  <img src="/arlo.png" alt="Arlo, by VotingWorks" />
                </Link>
              </NavbarHeading>
            </NavbarGroup>
          </InnerBar>
        </Nav>
      )}
    </>
  )
}

export default Header
