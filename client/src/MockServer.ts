import { setupServer, SetupServerApi } from 'msw/node'
import { http, HttpHandler, HttpResponse } from 'msw'
import {
  ITallyEntryAccountStatus,
  ITallyEntryLoginRequest,
} from './components/JurisdictionAdmin/BatchRoundSteps/TallyEntryAccountsStep'
import {
  IBatch,
  IBatches,
} from './components/JurisdictionAdmin/useBatchResults'
import { IContest } from './types'

export interface ITallyEntryAccountStatusWithPins
  extends ITallyEntryAccountStatus {
  loginRequests: Array<ITallyEntryLoginRequestWithPin>
}

export interface ITallyEntryLoginRequestWithPin
  extends ITallyEntryLoginRequest {
  pin: string
}

type ElectionId = string
type JurisdictionId = string
type RoundId = string

interface MockServerData {
  elections: Map<ElectionId, ElectionData>
}

interface ElectionData {
  jurisdictions: Map<JurisdictionId, JurisdictionData>
}

interface JurisdictionData {
  rounds: Map<RoundId, IBatches>
  contests: IContest[]
  tallyEntryAccountStatus: ITallyEntryAccountStatusWithPins
}

/**
 * The default election ID to use when mutating server state.
 */
export const DEFAULT_ELECTION_ID = '1'

/**
 * The default jurisdiction iD to use when mutating server state.
 */
export const DEFAULT_JURISDICTION_ID = 'jurisdiction-id-1'

/**
 * The default round iD to use when mutating server state.
 */
export const DEFAULT_ROUND_ID = 'round-1'

/**
 * A stateful mock server for Arlo built on top of `msw`'s mock server. Provides
 * the same basic API for using the mock server within tests or development,
 * plus methods for directly accessing the underlying state used by requests.
 */
export default class MockServer {
  /**
   * Server state.
   */
  private data: MockServerData = {
    elections: new Map(),
  }

  /**
   * Underlying `msw` server.
   */
  private readonly mswServer: ReturnType<typeof setupServer>

  private getOrCreateJurisdictionData(
    electionId: string,
    jurisdictionId: string
  ): JurisdictionData {
    if (typeof electionId !== 'string')
      throw new Error(`electionId is not a string: ${electionId}`)
    if (typeof jurisdictionId !== 'string')
      throw new Error(`jurisdictionId is not a string: ${jurisdictionId}`)
    let electionData = this.data.elections.get(electionId)

    if (!electionData) {
      electionData = { jurisdictions: new Map() }
      this.data.elections.set(electionId, electionData)
    }

    let jurisdictionData = electionData.jurisdictions.get(jurisdictionId)

    if (!jurisdictionData) {
      jurisdictionData = {
        rounds: new Map(),
        contests: [],
        tallyEntryAccountStatus: { passphrase: null, loginRequests: [] },
      }
      electionData.jurisdictions.set(jurisdictionId, jurisdictionData)
    }

    return jurisdictionData
  }

  constructor() {
    this.mswServer = setupServer(
      http.get<{
        electionId: string
        jurisdictionId: string
        roundId: string
      }>(
        '/api/election/:electionId/jurisdiction/:jurisdictionId/round/:roundId/batches',
        ({ params }) => {
          const data = this.getOrCreateJurisdictionData(
            params.electionId,
            params.jurisdictionId
          )
          const roundBatches: IBatches = data.rounds.get(params.roundId) ?? {
            batches: [],
            resultsFinalizedAt: null,
          }
          return HttpResponse.json(roundBatches)
        }
      ),
      http.post<{
        electionId: string
        jurisdictionId: string
        roundId: string
      }>(
        '/api/election/:electionId/jurisdiction/:jurisdictionId/round/:roundId/batches/finalize',
        ({ params }) => {
          const data = this.getOrCreateJurisdictionData(
            params.electionId,
            params.jurisdictionId
          )
          const roundBatches = data.rounds.get(params.roundId)

          if (!roundBatches) {
            return new HttpResponse('Not Found', { status: 404 })
          }

          if (roundBatches.resultsFinalizedAt) {
            return new HttpResponse('Results have already been finalized', {
              status: 409,
            })
          }

          roundBatches.resultsFinalizedAt = new Date().toISOString()
          return HttpResponse.json({ status: 'ok' })
        }
      ),
      http.get<{ electionId: string; jurisdictionId: string }>(
        '/auth/tallyentry/election/:electionId/jurisdiction/:jurisdictionId',
        ({ params }) => {
          const data = this.getOrCreateJurisdictionData(
            params.electionId,
            params.jurisdictionId
          )
          return HttpResponse.json(data.tallyEntryAccountStatus)
        }
      ),
      http.get<{ electionId: string; jurisdictionId: string }>(
        '/api/election/:electionId/jurisdiction/:jurisdictionId/contest',
        ({ params }) => {
          const data = this.getOrCreateJurisdictionData(
            params.electionId,
            params.jurisdictionId
          )
          return HttpResponse.json({ contests: data.contests })
        }
      ),
      http.post<{ electionId: string; jurisdictionId: string }>(
        '/auth/tallyentry/election/:electionId/jurisdiction/:jurisdictionId',
        ({ params }) => {
          const data = this.getOrCreateJurisdictionData(
            params.electionId,
            params.jurisdictionId
          )
          data.tallyEntryAccountStatus.passphrase = 'fixed-test-passphrase'
          return HttpResponse.json({ status: 'ok' })
        }
      ),
      http.post<{ electionId: string; jurisdictionId: string }>(
        '/auth/tallyentry/election/:electionId/jurisdiction/:jurisdictionId/confirm',
        async ({ params, request }) => {
          const body = (await request.json()) as {
            tallyEntryUserId: string
            loginCode: string
          }
          const data = this.getOrCreateJurisdictionData(
            params.electionId,
            params.jurisdictionId
          )
          const loginRequest = data.tallyEntryAccountStatus.loginRequests.find(
            lr => lr.tallyEntryUserId === body.tallyEntryUserId
          )

          if (!loginRequest) {
            return new HttpResponse('Not Found', { status: 404 })
          }

          if (body.loginCode !== loginRequest.pin) {
            return HttpResponse.json(
              {
                errors: [
                  {
                    errorType: 'Bad Request',
                    message: 'Invalid code, please try again.',
                  },
                ],
              },
              { status: 400 }
            )
          }

          loginRequest.loginConfirmedAt = new Date().toISOString()
          return HttpResponse.json({ status: 'ok' })
        }
      ),
      http.post<{ electionId: string; jurisdictionId: string }>(
        '/auth/tallyentry/election/:electionId/jurisdiction/:jurisdictionId/reject',
        async ({ params, request }) => {
          const body = (await request.json()) as { tallyEntryUserId: string }
          const data = this.getOrCreateJurisdictionData(
            params.electionId,
            params.jurisdictionId
          )
          const loginRequestIndex = data.tallyEntryAccountStatus.loginRequests.findIndex(
            lr => lr.tallyEntryUserId === body.tallyEntryUserId
          )

          if (loginRequestIndex < 0) {
            return new HttpResponse('Not Found', { status: 404 })
          }

          data.tallyEntryAccountStatus.loginRequests.splice(
            loginRequestIndex,
            1
          )
          return HttpResponse.json({ status: 'ok' })
        }
      )
    )
  }

  /**
   * Starts listening for requests with the underlying `msw` server, triggering
   * errors on unhandled requests by default.
   */
  listen(options?: Parameters<SetupServerApi['listen']>[0]): void {
    this.mswServer.listen({ onUnhandledRequest: 'error', ...options })
  }

  /**
   * Resets handlers in the underlying `msw` server and resets the server data.
   */
  resetHandlers(
    ...nextHandlers: Parameters<SetupServerApi['resetHandlers']>
  ): void {
    this.resetData()
    this.mswServer.resetHandlers(...nextHandlers)
  }

  /**
   * Closes the underlying `msw` server and resets the server data.
   */
  close(): void {
    this.resetData()
    this.mswServer.close()
  }

  use(...handlers: Parameters<SetupServerApi['use']>): this {
    this.mswServer.use(...handlers)
    return this
  }

  /**
   * Resets the stateful data held by this mock server that is used to respond
   * to requests. Called by {@link resetHandlers} and {@link close}.
   */
  resetData(): void {
    this.data = { elections: new Map() }
  }

  /**
   * Adds a batch to the mock server to be used in any subsequent requests. Will
   * be associated with the default election/jurisdiction unless you specify
   * different ones.
   */
  addBatch(
    batch: IBatch,
    {
      electionId = DEFAULT_ELECTION_ID,
      jurisdictionId = DEFAULT_JURISDICTION_ID,
      roundId = DEFAULT_ROUND_ID,
    }: {
      electionId?: ElectionId
      jurisdictionId?: JurisdictionId
      roundId?: RoundId
    } = {}
  ): this {
    const data = this.getOrCreateJurisdictionData(electionId, jurisdictionId)
    let round = data.rounds.get(roundId)
    if (!round) {
      round = {
        batches: [],
        resultsFinalizedAt: null,
      }
      data.rounds.set(roundId, round)
    }
    round.batches.push(batch)
    return this
  }

  /**
   * Adds a contest to the mock server to be used in any subsequent requests.
   * Will be associated with the default election/jurisdiction unless you
   * specify different ones.
   */
  addContest(
    contest: IContest,
    {
      electionId = DEFAULT_ELECTION_ID,
      jurisdictionId = DEFAULT_JURISDICTION_ID,
    }: { electionId?: ElectionId; jurisdictionId?: JurisdictionId } = {}
  ): this {
    const data = this.getOrCreateJurisdictionData(electionId, jurisdictionId)
    data.contests.push(contest)
    return this
  }

  /**
   * Gets the default tally account passphrase. You can set or clear this value
   * using {@link setTallyAccountPassphrase}.
   */

  getTallyAccountPassphrase({
    electionId = DEFAULT_ELECTION_ID,
    jurisdictionId = DEFAULT_JURISDICTION_ID,
  }: { electionId?: string; jurisdictionId?: string } = {}): string | null {
    const data = this.getOrCreateJurisdictionData(electionId, jurisdictionId)
    return data.tallyEntryAccountStatus.passphrase
  }

  /**
   * Sets or clears the default tally account passphrase.
   */
  setTallyAccountPassphrase(
    passphrase: string | null,
    {
      electionId = DEFAULT_ELECTION_ID,
      jurisdictionId = DEFAULT_JURISDICTION_ID,
    }: { electionId?: string; jurisdictionId?: string } = {}
  ): this {
    const data = this.getOrCreateJurisdictionData(electionId, jurisdictionId)
    data.tallyEntryAccountStatus.passphrase = passphrase
    return this
  }

  /**
   * Adds a login request to the mock server be used in any subsequent requests.
   * Will be associated with the default election/jurisdiction unless you
   * specify different ones.
   */
  addLoginRequest(
    loginRequest: ITallyEntryLoginRequestWithPin,
    {
      electionId = DEFAULT_ELECTION_ID,
      jurisdictionId = DEFAULT_JURISDICTION_ID,
    }: { electionId?: string; jurisdictionId?: string } = {}
  ): this {
    const data = this.getOrCreateJurisdictionData(electionId, jurisdictionId)
    data.tallyEntryAccountStatus.loginRequests.push(loginRequest)
    return this
  }
}

export const server = new MockServer()
