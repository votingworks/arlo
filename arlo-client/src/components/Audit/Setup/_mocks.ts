import { ElementType } from '../../../types'
import { setupStages } from './index'
import { ISidebarMenuItem } from '../../Atoms/Sidebar'

const relativeStages = (s: ElementType<typeof setupStages>) => {
  const prevTitle = setupStages[setupStages.indexOf(s) - 1]
  const prevStage: ISidebarMenuItem = {
    title: prevTitle,
    active: false,
    activate: jest.fn(),
    state: 'live',
  }
  const nextTitle = setupStages[setupStages.indexOf(s) + 1]
  const nextStage: ISidebarMenuItem = {
    title: nextTitle,
    active: false,
    activate: jest.fn(),
    state: 'live',
  }
  return { prevStage, nextStage }
}

export default relativeStages
