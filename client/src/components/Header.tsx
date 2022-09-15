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
import { useAuthDataContext, IAuditBoardMember } from './UserContext'
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
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  a.title {
    display: flex;
    text-decoration: none;
    color: ${Colors.DARK_GRAY2};
    font-size: 1.1rem;
    font-weight: bold;
    img {
      position: relative;
      bottom: 2px;
      margin-right: 7px;
    }
  }
  @media only screen and (max-width: 767px) {
    justify-content: center;
  }
`

interface TParams {
  electionId: string
  jurisdictionId?: string
}

const Header: React.FC = () => {
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

  if (auth && auth.user && auth.user.type === 'audit_board') return null

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
      {!supportMatch && (
        <Nav>
          <InnerBar>
            <NavbarGroup align={Alignment.LEFT}>
              <NavbarHeading>
                <Link to="/" className="title">
                  <img
                    src="/votingworks-logo-circle.png"
                    alt="Arlo, by VotingWorks"
                  />
                  <span>Arlo</span>
                </Link>
              </NavbarHeading>
              {jurisdiction && (
                <NavbarHeading>Jurisdiction: {jurisdiction.name}</NavbarHeading>
              )}
            </NavbarGroup>
            {auth && auth.user && auth.user.type !== 'audit_board' && (
              <>
                <NavbarGroup align={Alignment.RIGHT}>
                  {auth.user.type === 'audit_admin' && (
                    <>
                      {electionId && (
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
                          <NavbarDivider />
                        </>
                      )}
                      <LinkButton to="/" minimal icon="projects">
                        All Audits
                      </LinkButton>
                      <LinkButton to="/activity" minimal icon="history">
                        Activity Log
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
              </>
            )}
          </InnerBar>
        </Nav>
      )}
    </>
  )
}

interface IHeaderAuditBoardProps {
  boardName: string
  members: IAuditBoardMember[]
}

export const HeaderAuditBoard: React.FC<IHeaderAuditBoardProps> = ({
  boardName,
  members,
}: IHeaderAuditBoardProps) => {
  return (
    <Nav>
      <InnerBar>
        <NavbarGroup align={Alignment.LEFT}>
          <NavbarHeading>
            <Link to="/" className="title">
              <img
                src="/votingworks-logo-circle.png"
                alt="Arlo, by VotingWorks"
              />
              <span>Arlo</span>
            </Link>
          </NavbarHeading>
          <NavbarHeading>
            {boardName}
            {members.length > 0 && (
              <>
                :{' '}
                <strong>{members.map(member => member.name).join(', ')}</strong>
              </>
            )}
          </NavbarHeading>
        </NavbarGroup>
        <NavbarGroup align={Alignment.RIGHT}>
          <a href="/auth/logout">
            {' '}
            <span>Log out</span>{' '}
          </a>
        </NavbarGroup>
      </InnerBar>
    </Nav>
  )
}

export default Header
