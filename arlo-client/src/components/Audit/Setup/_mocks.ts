import { ElementType } from '../../../types'
import { setupStages } from './index'
import { ISidebarMenuItem } from '../../Atoms/Sidebar'

const relativeStages = (
  stage: ElementType<typeof setupStages>,
  state: ISidebarMenuItem['state'] = 'live'
) => {
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
  return { prevStage, nextStage }
}

export default relativeStages
