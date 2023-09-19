import React from 'react'
import styled from 'styled-components'
import { Menu, IMenuItemProps } from '@blueprintjs/core'
import H2Title from './H2Title'

const Wrapper = styled.div`
  margin-right: 30px;
  width: 250px;
  flex-shrink: 0;

  ul.bp3-menu {
    padding: 0;
    .bp3-menu-item {
      padding: 10px 15px;
      border-radius: 0;
    }
    .bp3-menu-divider {
      margin: 0;
    }
  }
`

export interface ISidebarMenuItem
  extends Pick<IMenuItemProps, 'text' | 'active' | 'disabled' | 'onClick'> {
  id: string
}

interface IProps {
  title: string
  menuItems: ISidebarMenuItem[]
}

const Sidebar: React.FC<IProps> = ({ menuItems, title }) => (
  <Wrapper>
    <H2Title>{title}</H2Title>
    <Menu>
      {menuItems.map((item, i) => {
        return (
          <React.Fragment key={item.id}>
            {i > 0 && <Menu.Divider />}
            <Menu.Item {...item} role="link" />
          </React.Fragment>
        )
      })}
    </Menu>
  </Wrapper>
)

export default Sidebar
