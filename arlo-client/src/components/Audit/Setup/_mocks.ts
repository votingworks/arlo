import { ElementType } from '../../../types'
import { setupStages } from './index'
import { ISidebarMenuItem } from '../../Atoms/Sidebar'

const relativeStages = (
  stage: ElementType<typeof setupStages>,
  state: ISidebarMenuItem['state'] = 'live'
): {
  prevStage: ISidebarMenuItem
  nextStage: ISidebarMenuItem
  menuItems: ISidebarMenuItem[]
} => {
  const prevTitle = setupStages[setupStages.indexOf(stage) - 1]
  const prevStage: ISidebarMenuItem = {
    title: prevTitle,
    active: false,
    activate: jest.fn(),
    state,
  }
  const nextTitle = setupStages[setupStages.indexOf(stage) + 1]
  const nextStage: ISidebarMenuItem = {
    title: nextTitle,
    active: false,
    activate: jest.fn(),
    state,
  }
  const menuItems = setupStages.map((s: ElementType<typeof setupStages>) => ({
    title: s,
    active: s === stage,
    activate: jest.fn(),
    state,
  }))
  return { prevStage, nextStage, menuItems }
}

export default relativeStages
