import React from 'react'
import styled from 'styled-components'
import { Menu, Spinner, IMenuItemProps } from '@blueprintjs/core'
import H2Title from './H2Title'

const Wrapper = styled.div`
  margin-right: 30px;
  width: 250px;

  ul.bp3-menu {
    padding-left: 0;
  }
`

export interface ISidebarMenuItem {
  id: string
  activate?: (e?: unknown | null, force?: boolean) => void
  title: string
  active: boolean
  state: 'live' | 'processing' | 'locked'
}

interface IProps {
  menuItems: ISidebarMenuItem[]
  title: string
}

const Sidebar = ({ menuItems, title }: IProps): React.ReactElement => (
  <Wrapper>
    <H2Title>{title}</H2Title>
    <Menu>
      {menuItems.map((item, i) => {
        const itemProps: IMenuItemProps = {
          active: item.active,
          text: item.title,
          disabled: item.state !== 'live',
          labelElement:
            item.state === 'processing' ? (
              <Spinner size={Spinner.SIZE_SMALL} />
            ) : null,
        }
        if (item.activate) itemProps.onClick = item.activate
        return (
          <React.Fragment key={item.id}>
            {i > 0 && <Menu.Divider />}
            <Menu.Item {...itemProps} />
          </React.Fragment>
        )
      })}
    </Menu>
  </Wrapper>
)

export default Sidebar
