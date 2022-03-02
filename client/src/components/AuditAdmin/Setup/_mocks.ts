import { ElementType } from '../../../types'
import { setupStages, stageTitles } from './Setup'
import { ISidebarMenuItem } from '../../Atoms/Sidebar'

const relativeStages = (
  stage: ElementType<typeof setupStages>,
  state: ISidebarMenuItem['state'] = 'live'
): {
  prevStage: ISidebarMenuItem
  nextStage: ISidebarMenuItem
  menuItems: ISidebarMenuItem[]
} => {
  const prevId = setupStages[setupStages.indexOf(stage) - 1]
  const prevStage: ISidebarMenuItem = {
    id: prevId,
    title: stageTitles[prevId],
    active: false,
    activate: jest.fn(),
    state,
  }
  const nextId = setupStages[setupStages.indexOf(stage) + 1]
  const nextStage: ISidebarMenuItem = {
    id: nextId,
    title: stageTitles[nextId],
    active: false,
    activate: jest.fn(),
    state,
  }
  const menuItems = setupStages.map((s: ElementType<typeof setupStages>) => ({
    id: s,
    title: stageTitles[s],
    active: s === stage,
    activate: jest.fn(),
    state,
  }))
  return { prevStage, nextStage, menuItems }
}

export default relativeStages
