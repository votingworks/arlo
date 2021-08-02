import React from 'react'
import styled from 'styled-components'
import {
  Navbar,
  NavbarGroup,
  NavbarHeading,
  Alignment,
} from '@blueprintjs/core'
import { Link } from 'react-router-dom'
import { Inner } from '../Atoms/Wrapper'
import { IAuditBoardMember } from '../UserContext'

interface IProps {
  boardName: string
  members: IAuditBoardMember[]
}

const Nav = styled(Navbar)`
  width: 100%;
  height: auto;
  padding: 0;
  .bp3-navbar-heading img {
    height: 35px;
    padding-top: 5px;
  }
`

const InnerBar = styled(Inner)`
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  .logo-mobile {
    display: none;
  }
  @media only screen and (max-width: 767px) {
    justify-content: center;
    .logo-desktop {
      display: none;
    }
    .logo-mobile {
      display: block;
    }
  }
`

const HeaderDataEntry: React.FC<IProps> = ({ boardName, members }: IProps) => {
  return (
    <Nav>
      <InnerBar>
        <NavbarGroup align={Alignment.LEFT}>
          <NavbarHeading>
            <Link to="/">
              <img
                src="/arlo.png"
                alt="Arlo, by VotingWorks"
                className="logo-desktop"
              />
              <img
                src="/arlo-mobile.png"
                alt="Arlo, by VotingWorks"
                className="logo-mobile"
              />
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
export default HeaderDataEntry
