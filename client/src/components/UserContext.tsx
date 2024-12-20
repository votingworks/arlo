import React, {
  createContext,
  useState,
  useEffect,
  useMemo,
  useContext,
} from 'react'
import { api } from './utilities'

export interface IElection {
  id: string
  auditName: string
  electionName: string
  state: string
  createdAt: string
  isComplete: boolean
}

export interface IOrganization {
  id: string
  name: string
  elections: IElection[]
}

export interface IJurisdiction {
  id: string
  name: string
  election: IElection & { organizationId: string }
  numBallots: number | null
}

export interface IAuditAdmin {
  type: 'audit_admin'
  name: string
  email: string
  id: string
}

export interface IJurisdictionAdmin {
  type: 'jurisdiction_admin'
  name: string
  email: string
  organizations: []
  jurisdictions: IJurisdiction[]
}

export interface IMember {
  name: string
  affiliation: string | null
}

export interface IAuditBoard {
  type: 'audit_board'
  id: string
  name: string
  jurisdictionId: string
  jurisdictionName: string
  electionId: string
  roundId: string
  members: IMember[]
  signedOffAt: string | null
}

export interface ITallyEntryUser {
  type: 'tally_entry'
  id: string
  loginCode: string | null
  loginConfirmedAt: string | null
  jurisdictionId: string
  jurisdictionName: string
  electionId: string
  roundId: string
  auditName: string
  members: IMember[]
}

export type IUser =
  | IAuditAdmin
  | IJurisdictionAdmin
  | IAuditBoard
  | ITallyEntryUser

export interface ISupportUser {
  email: string
}

export interface IAuthData {
  user: IUser | null
  supportUser: ISupportUser | null
}

const AuthDataContext = createContext<IAuthData | null>(null)

const AuthDataProvider: React.FC = props => {
  const [authData, setAuthData] = useState<IAuthData | null>(null)

  useEffect(() => {
    ;(async () => {
      const response = await api<IAuthData>('/me')
      setAuthData(response)
    })()
  }, [])

  const authDataValue = useMemo(() => authData && { ...authData }, [authData])

  return <AuthDataContext.Provider value={authDataValue} {...props} />
}

export const useAuthDataContext = (): IAuthData | null =>
  useContext(AuthDataContext)

export default AuthDataProvider
