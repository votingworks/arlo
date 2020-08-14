import React, { useContext } from 'react'
import { waitFor, fireEvent, render, screen } from '@testing-library/react'
import {
  BrowserRouter as Router,
  Router as RegularRouter,
  useParams,
} from 'react-router-dom'
import { AuditAdminView, JurisdictionAdminView } from './index'
import { auditSettings, manifestMocks, talliesMocks } from './_mocks'
import * as utilities from '../utilities'
import {
  routerTestProps,
  withMockFetch,
  renderWithRouter,
} from '../testUtilities'
import AuthDataProvider, { AuthDataContext } from '../UserContext'
import getJurisdictionFileStatus, {
  FileProcessingStatus,
} from './useSetupMenuItems/getJurisdictionFileStatus'
import getRoundStatus from './useSetupMenuItems/getRoundStatus'
import { contestMocks } from './AASetup/Contests/_mocks'
import { IFileInfo } from './useJurisdictions'

const getJurisdictionFileStatusMock = getJurisdictionFileStatus as jest.Mock
const getRoundStatusMock = getRoundStatus as jest.Mock

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
  checkAndToastMock.mockClear()
  paramsMock.mockReturnValue({
    electionId: '1',
    view: 'setup',
  })
})

describe.skip('AA setup flow', () => {
  const apiCalls = {
    getUser: {
      url: '/api/me',
      response: {
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
      },
    },
    getRounds: {
      url: '/api/election/1/round',
      response: { rounds: [] },
    },
    getJurisdictions: {
      url: '/api/election/1/jurisdiction',
      response: {
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
      },
    },
    getJurisdictionFile: {
      url: '/api/election/1/jurisdiction/file',
      response: {
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
      },
    },
    getContests: {
      url: '/api/election/1/contest',
      response: contestMocks.filledTargeted,
    },
    getSettings: {
      url: '/api/election/1/settings',
      response: auditSettings.all,
    },
    putSettings: {
      url: '/api/election/1/settings',
      options: {
        method: 'PUT',
        body: JSON.stringify(auditSettings.all),
        headers: { 'Content-Type': 'application/json' },
      },
      response: { status: 'ok' },
    },
    getSampleSizes: {
      url: '/api/election/1/sample-sizes',
      response: { sampleSizes: null },
    },
  }

  // AuditAdminView will only be rendered once the user is logged in, so
  // we simulate that.
  const AuditAdminViewWithAuth: React.FC = () => {
    const { isAuthenticated } = useContext(AuthDataContext)
    return isAuthenticated ? <AuditAdminView /> : null
  }

  const loadEach = [
    apiCalls.getRounds,
    apiCalls.getJurisdictions,
    apiCalls.getContests,
    apiCalls.getSettings,
  ]

  it('sidebar changes stages', async () => {
    const expectedCalls = [
      apiCalls.getUser,
      ...loadEach,
      ...loadEach,
      apiCalls.getSettings,
      apiCalls.getJurisdictionFile,
      apiCalls.getSettings,
      ...loadEach,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { queryAllByText, getByText } = render(
        <AuthDataProvider>
          <Router>
            <AuditAdminViewWithAuth />
          </Router>
        </AuthDataProvider>
      )

      await waitFor(() => {
        expect(queryAllByText('Participants').length).toBe(2)
      })

      fireEvent.click(getByText('Audit Settings'), { bubbles: true })

      await waitFor(() => {
        expect(queryAllByText('Audit Settings').length).toBe(2)
      })
    })
  })

  it('next and back buttons change stages', async () => {
    const expectedCalls = [
      apiCalls.getUser,
      ...loadEach,
      ...loadEach,
      apiCalls.getSettings,
      apiCalls.getJurisdictionFile,
      apiCalls.getSettings,
      ...loadEach,
      apiCalls.getSettings,
      apiCalls.putSettings,
      ...loadEach,
      apiCalls.getSettings,
      apiCalls.getJurisdictions,
      apiCalls.getJurisdictionFile,
      apiCalls.getContests,
      apiCalls.getSampleSizes,
      apiCalls.getSettings,
      ...loadEach,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { queryAllByText, getByText } = render(
        <AuthDataProvider>
          <Router>
            <AuditAdminViewWithAuth />
          </Router>
        </AuthDataProvider>
      )

      await waitFor(() => {
        expect(queryAllByText('Participants').length).toBe(2)
      })

      fireEvent.click(getByText('Audit Settings'), { bubbles: true })

      await waitFor(() => {
        expect(queryAllByText('Audit Settings').length).toBe(2)
      })

      fireEvent.click(getByText('Save & Next'))
      await waitFor(() => {
        expect(queryAllByText('Review & Launch').length).toBe(2)
      })
      fireEvent.click(getByText('Back'))
      await waitFor(() => {
        expect(queryAllByText('Audit Settings').length).toBe(2)
      })
    })
  })

  it('renders sidebar when authenticated on /setup', async () => {
    const expectedCalls = [
      apiCalls.getUser,
      ...loadEach,
      ...loadEach,
      apiCalls.getSettings,
      apiCalls.getJurisdictionFile,
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container, queryAllByText } = render(
        <AuthDataProvider>
          <Router>
            <AuditAdminViewWithAuth />
          </Router>
        </AuthDataProvider>
      )

      await waitFor(() => {
        expect(queryAllByText('Participants').length).toBe(2)
        expect(container).toMatchSnapshot()
      })
    })
  })

  it('renders sidebar when authenticated on /progress', async () => {
    paramsMock.mockReturnValue({
      electionId: '1',
      view: 'progress',
    })
    const expectedCalls = [apiCalls.getUser, ...loadEach, ...loadEach]
    await withMockFetch(expectedCalls, async () => {
      const { container, queryAllByText } = render(
        <AuthDataProvider>
          <Router>
            <AuditAdminViewWithAuth />
          </Router>
        </AuthDataProvider>
      )

      await waitFor(() => {
        expect(queryAllByText('Jurisdictions').length).toBe(1)
        expect(container).toMatchSnapshot()
      })
    })
  })

  it('redirects to /progress by default', async () => {
    const expectedCalls = [apiCalls.getUser, ...loadEach, ...loadEach]
    const routeProps = routerTestProps('/election/1', { electionId: '1' })
    await withMockFetch(expectedCalls, async () => {
      paramsMock.mockReturnValue({
        electionId: '1',
        view: '',
      })
      render(
        <AuthDataProvider>
          <RegularRouter {...routeProps}>
            <AuditAdminViewWithAuth />
          </RegularRouter>
        </AuthDataProvider>
      )
      await waitFor(() => {
        expect(routeProps.history.location.pathname).toEqual(
          '/election/1/progress'
        )
      })
    })
  })
})

describe('JA setup', () => {
  const apiCalls = {
    getUser: {
      url: '/api/me',
      response: {
        type: 'jurisdiction_admin',
        name: 'Joe',
        email: 'test@email.org',
        jurisdictions: [
          {
            id: 'jurisdiction-id-1',
            name: 'Jurisdiction One',
            election: {
              id: '1',
              auditName: 'audit one',
              electionName: 'election one',
              state: 'AL',
              isMultiJurisdiction: true,
            },
          },
          {
            id: 'jurisdiction-id-2',
            name: 'Jurisdiction Two',
            election: {
              id: '1',
              auditName: 'audit one',
              electionName: 'election one',
              state: 'AL',
              isMultiJurisdiction: true,
            },
          },
        ],
        organizations: [],
      },
    },
    getRounds: {
      url: '/api/election/1/jurisdiction/jurisdiction-id-1/round',
      response: { rounds: [] },
    },
    getBallotManifestFile: (response: IFileInfo) => ({
      url: '/api/election/1/jurisdiction/jurisdiction-id-1/ballot-manifest',
      response,
    }),
    getBatchTalliesFile: (response: IFileInfo) => ({
      url: '/api/election/1/jurisdiction/jurisdiction-id-1/batch-tallies',
      response,
    }),
    getSettings: {
      url: '/api/election/1/jurisdiction/jurisdiction-id-1/settings',
      response: auditSettings.all,
    },
  }

  // JurisdictionAdminView will only be rendered once the user is logged in, so
  // we simulate that.
  const JurisdictionAdminViewWithAuth: React.FC = () => {
    const { isAuthenticated } = useContext(AuthDataContext)
    return isAuthenticated ? <JurisdictionAdminView /> : null
  }

  const renderView = () =>
    renderWithRouter(
      <AuthDataProvider>
        <JurisdictionAdminViewWithAuth />
      </AuthDataProvider>,
      {
        route: '/election/1/jurisdiction/jurisdiction-id-1/setup',
      }
    )

  beforeEach(() => {
    paramsMock.mockReturnValue({
      electionId: '1',
      jurisdictionId: 'jurisdiction-id-1',
      view: 'setup',
    })
  })

  it('renders initial state', async () => {
    const expectedCalls = [
      apiCalls.getUser,
      apiCalls.getSettings,
      apiCalls.getRounds,
      apiCalls.getBallotManifestFile(manifestMocks.empty),
      apiCalls.getBatchTalliesFile(talliesMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderView()
      await screen.findByText('Audit Source Data')
      expect(container).toMatchSnapshot()
    })
  })
})
