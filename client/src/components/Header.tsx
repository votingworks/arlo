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
import { useAuthDataContext, IMember } from './UserContext'
import { Inner } from './Atoms/Wrapper'
import LinkButton from './Atoms/LinkButton'

const VisuallyHiddenFocusableAnchor = styled.a`
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
  border: 0;

  &:focus,
  &:focus-visible {
    position: static;
    width: auto;
    height: auto;
    margin: 0 0.5rem 0 0;
    overflow: visible;
    clip: auto;
    white-space: normal;
  }
`

const SupportBar = styled(Navbar)`
  background-color: ${Colors.ROSE3};
  height: 35px;
  padding: 0 150px;
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

  @media (max-width: 480px) {
    padding: 10px;
  }
`

const StyledNavbarInner = styled(Navbar)`
  width: 100%;
  height: auto;
  padding: 0;
  .bp3-navbar-heading img {
    height: 35px;
  }
`

function Nav(
  props: React.ComponentProps<typeof Navbar> & { wrappingAriaLabel: string }
) {
  // Wraps in <nav> because Blueprint's Navbar does not set the <nav> landmark itself
  return (
    <nav aria-label={props.wrappingAriaLabel} style={{ width: '100%' }}>
      <StyledNavbarInner {...props} aria-label={props.wrappingAriaLabel} />
    </nav>
  )
}

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
    font-weight: 700;
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
}

const Header: React.FC = () => {
  const electionMatch:
    | RouteComponentProps<TParams>['match']
    | null = useRouteMatch('/election/:electionId')
  const supportMatch = useRouteMatch('/support')
  const auth = useAuthDataContext()
  const electionId = electionMatch ? electionMatch.params.electionId : undefined

  if (
    auth &&
    auth.user &&
    (auth.user.type === 'audit_board' || auth?.user.type === 'tally_entry')
  )
    return null

  return (
    <>
      {auth && auth.supportUser && (
        <SupportBar>
          <NavbarGroup align={Alignment.LEFT}>
            <VisuallyHiddenFocusableAnchor tabIndex={0} href="#main">
              Skip to main content
            </VisuallyHiddenFocusableAnchor>
            <a href="/support">
              <Icon icon="eye-open" />
              <span style={{ fontWeight: 600 }}>Arlo Support Tools</span>
            </a>
          </NavbarGroup>
          <NavbarGroup align={Alignment.RIGHT}>
            <span>{auth.supportUser.email}</span>
            <NavbarDivider />
            <a href="/auth/support/logout">Log out</a>
          </NavbarGroup>
        </SupportBar>
      )}
      {!supportMatch && (
        <Nav wrappingAriaLabel="Main navigation">
          <InnerBar>
            <NavbarGroup align={Alignment.LEFT}>
              <VisuallyHiddenFocusableAnchor tabIndex={0} href="#main">
                Skip to main content
              </VisuallyHiddenFocusableAnchor>
              <NavbarHeading>
                <Link to="/" className="title">
                  <img
                    src="/votingworks-logo-circle.png"
                    alt="Arlo, by VotingWorks"
                  />
                  <span>Arlo</span>
                </Link>
              </NavbarHeading>
            </NavbarGroup>
            {auth &&
              auth.user &&
              auth.user.type !== 'audit_board' &&
              auth.user.type !== 'tally_entry' && (
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
  members: IMember[]
}

export const HeaderAuditBoard: React.FC<IHeaderAuditBoardProps> = ({
  boardName,
  members,
}: IHeaderAuditBoardProps) => {
  return (
    <Nav wrappingAriaLabel="Main navigation">
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

export const HeaderTallyEntry: React.FC = () => (
  <Nav wrappingAriaLabel="Main navigation">
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

export default Header
