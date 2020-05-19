import React, { useContext } from 'react'
import { wait, fireEvent } from '@testing-library/react'
import {
  BrowserRouter as Router,
  Router as RegularRouter,
  useParams,
} from 'react-router-dom'
import { AuditAdminView } from './index'
import { auditSettings } from './_mocks'
import * as utilities from '../utilities'
import { asyncActRender, routerTestProps } from '../testUtilities'
import AuthDataProvider, { AuthDataContext } from '../UserContext'
import getJurisdictionFileStatus, {
  FileProcessingStatus,
} from './useSetupMenuItems/getJurisdictionFileStatus'
import getRoundStatus from './useSetupMenuItems/getRoundStatus'
import { contestMocks } from './Setup/Contests/_mocks'

const getJurisdictionFileStatusMock = getJurisdictionFileStatus as jest.Mock
const getRoundStatusMock = getRoundStatus as jest.Mock

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()
const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)

checkAndToastMock.mockReturnValue(false)

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'), // use actual for all non-hook parts
  useRouteMatch: jest.fn(),
  useParams: jest.fn(),
}))
const paramsMock = useParams as jest.Mock
paramsMock.mockReturnValue({
  electionId: '1',
  view: 'setup',
})

jest.mock('./useSetupMenuItems/getJurisdictionFileStatus')
jest.mock('./useSetupMenuItems/getRoundStatus')
getJurisdictionFileStatusMock.mockReturnValue('PROCESSED')
getRoundStatusMock.mockReturnValue(false)

afterEach(() => {
  apiMock.mockClear()
  checkAndToastMock.mockClear()
  paramsMock.mockReturnValue({
    electionId: '1',
    view: 'setup',
  })
})

describe('AA setup flow', () => {
  // AuditAdminView will only be rendered once the user is logged in, so
  // we simulate that.
  const AuditAdminViewWithAuth: React.FC = () => {
    const { isAuthenticated } = useContext(AuthDataContext)
    return isAuthenticated ? <AuditAdminView /> : null
  }

  beforeEach(() =>
    apiMock.mockImplementation(async (endpoint: string) => {
      switch (endpoint) {
        case '/auth/me':
          return {
            type: 'audit_admin',
            name: 'Joe',
            email: 'test@email.org',
            jurisdictions: [],
            organizations: [
              {
                id: 'org-id',
                name: 'State',
                elections: [],
              },
            ],
          }
        case '/election/1/round':
          return { rounds: [] }
        case '/election/1/jurisdiction':
          return {
            jurisdictions: [
              {
                id: 'jurisdiction-id-1',
                name: 'Jurisdiction One',
                ballotManifest: { file: null, processing: null },
                currentRoundStatus: null,
              },
              {
                id: 'jurisdiction-id-2',
                name: 'Jurisdiction Two',
                ballotManifest: { file: null, processing: null },
                currentRoundStatus: null,
              },
            ],
          }
        case '/election/1/jurisdiction/file':
          return {
            file: {
              contents: null,
              name: 'file name',
              uploadedAt: 'a long time ago in a galaxy far far away',
            },
            processing: {
              status: FileProcessingStatus.Processed,
              error: null,
              startedAt: 'once upon a time',
              endedAt: 'and they lived happily ever after',
            },
          }
        case '/election/1/contest':
          return contestMocks.filledTargeted
        case '/election/1/settings':
          return auditSettings.all
        default:
          return null
      }
    })
  )

  it('sidebar changes stages', async () => {
    const { queryAllByText, getByText } = await asyncActRender(
      <AuthDataProvider>
        <Router>
          <AuditAdminViewWithAuth />
        </Router>
      </AuthDataProvider>
    )

    await wait(() => {
      expect(queryAllByText('Participants').length).toBe(2)
    })

    fireEvent.click(getByText('Target Contests'), { bubbles: true })

    await wait(() => {
      expect(queryAllByText('Target Contests').length).toBe(2)
    })
  })

  it('next and back buttons change stages', async () => {
    const { queryAllByText, getByText } = await asyncActRender(
      <AuthDataProvider>
        <Router>
          <AuditAdminViewWithAuth />
        </Router>
      </AuthDataProvider>
    )

    await wait(() => {
      expect(queryAllByText('Participants').length).toBe(2)
    })

    fireEvent.click(getByText('Audit Settings'), { bubbles: true })

    await wait(() => {
      expect(queryAllByText('Audit Settings').length).toBe(2)
    })

    fireEvent.click(getByText('Save & Next'))
    await wait(() => {
      expect(queryAllByText('Review & Launch').length).toBe(2)
    })
    fireEvent.click(getByText('Back'))
    await wait(() => {
      expect(queryAllByText('Audit Settings').length).toBe(2)
    })
  })

  it('renders sidebar when authenticated on /setup', async () => {
    const { container, queryAllByText } = await asyncActRender(
      <AuthDataProvider>
        <Router>
          <AuditAdminViewWithAuth />
        </Router>
      </AuthDataProvider>
    )

    await wait(() => {
      expect(queryAllByText('Participants').length).toBe(2)
      expect(container).toMatchSnapshot()
    })
  })

  it('renders sidebar when authenticated on /progress', async () => {
    paramsMock.mockReturnValue({
      electionId: '1',
      view: 'progress',
    })
    const { container, queryAllByText } = await asyncActRender(
      <AuthDataProvider>
        <Router>
          <AuditAdminViewWithAuth />
        </Router>
      </AuthDataProvider>
    )

    await wait(() => {
      expect(queryAllByText('Jurisdictions').length).toBe(1)
      expect(container).toMatchSnapshot()
    })
  })

  it('redirects to /progress by default', async () => {
    const routeProps = routerTestProps('/election/1', { electionId: '1' })
    paramsMock.mockReturnValue({
      electionId: '1',
      view: '',
    })
    await asyncActRender(
      <AuthDataProvider>
        <RegularRouter {...routeProps}>
          <AuditAdminViewWithAuth />
        </RegularRouter>
      </AuthDataProvider>
    )
    await wait(() => {
      expect(routeProps.history.location.pathname).toEqual(
        '/election/1/progress'
      )
    })
  })
})
