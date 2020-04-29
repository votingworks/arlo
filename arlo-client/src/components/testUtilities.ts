import React from 'react'
import { RenderResult, act, render } from '@testing-library/react'
import { createLocation, createMemoryHistory } from 'history'
import { match as routerMatch } from 'react-router-dom'
import { IAudit, IUserMeta, IRound, IAuditSettings, IBallot } from '../types'
import { IJurisdictions } from './Audit/Setup/useParticipantsApi'
import { IContests } from './Audit/Setup/Contests/types'

type MatchParameter<Params> = { [K in keyof Params]?: string }

const generateUrl = <Params extends MatchParameter<Params>>(
  path: string,
  params: Params
): string => {
  let tempPath = path

  for (const param in params) {
    /* istanbul ignore else */
    if (Object.prototype.hasOwnProperty.call(params, param)) {
      const value = params[param]
      tempPath = tempPath.replace(`:${param}`, value as NonNullable<
        typeof value
      >)
    }
  }

  return tempPath
}

export const routerTestProps = <Params extends MatchParameter<Params> = {}>(
  path: string,
  params: Params
) => {
  const match: routerMatch<Params> = {
    isExact: false,
    path,
    url: generateUrl(path, params),
    params,
  }
  const history = createMemoryHistory()
  const location = createLocation(match.url)

  return { history, location, match }
}

/** Credit to https://stackoverflow.com/a/56452779 for solution to mocking React Router props */

export const regexpEscape = (s: string) => {
  /* eslint-disable no-useless-escape */
  return s.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')
}

export const asyncActRender = async (
  component: React.ReactElement
): Promise<RenderResult> => {
  let result: RenderResult
  await act(async () => {
    result = render(component)
  })
  return result!
}

export const generateApiMock = ({
  statusReturn,
  authReturn,
  roundReturn,
  jurisdictionReturn,
  settingsReturn,
  ballotsReturn,
  contestsReturn,
}: {
  statusReturn?: IAudit | Error | { status: 'ok' }
  authReturn?: IUserMeta | Error
  roundReturn?: { rounds: IRound[] } | Error | { status: 'ok' }
  jurisdictionReturn?:
    | { jurisdictions: IJurisdictions }
    | Error
    | { status: 'ok' }
  settingsReturn?: IAuditSettings | Error
  ballotsReturn?: { ballots: IBallot[] } | Error
  contestsReturn?: IContests | Error
}) => async (
  endpoint: string
): Promise<
  | IAudit
  | IUserMeta
  | { rounds: IRound[] }
  | { jurisdictions: IJurisdictions }
  | IAuditSettings
  | { ballots: IBallot[] }
  | IContests
  | Error
  | { status: 'ok' }
> => {
  if (endpoint === '/election/1/audit/status' && statusReturn)
    return statusReturn
  if (endpoint === '/auth/me' && authReturn) return authReturn
  if (endpoint === '/election/1/round' && roundReturn) return roundReturn
  if (endpoint === '/election/1/jurisdiction' && jurisdictionReturn)
    return jurisdictionReturn
  if (endpoint === '/election/1/settings' && settingsReturn)
    return settingsReturn
  if (
    endpoint.match(
      /\/election\/[^/]+\/jurisdiction\/[^/]+\/round\/[^/]+\/ballot-list/
    ) &&
    ballotsReturn
  )
    return ballotsReturn
  if (endpoint === '/election/1/contest' && contestsReturn)
    return contestsReturn
  return new Error(`missing mock for ${endpoint}`)
}

export default {
  routerTestProps,
}
