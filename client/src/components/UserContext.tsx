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
}

export interface IOrganization {
  id: string
  name: string
  elections: IElection[]
}

export interface IJurisdiction {
  id: string
  name: string
  election: IElection
  numBallots: number | null
}

export interface IAuditBoardMember {
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
  members: IAuditBoardMember[]
  signedOffAt: string | null
}

export interface IAuditAdmin {
  type: 'audit_admin'
  name: string
  email: string
  organizations: IOrganization[]
  jurisdictions: []
}

export interface IJurisdictionAdmin {
  type: 'jurisdiction_admin'
  name: string
  email: string
  organizations: []
  jurisdictions: IJurisdiction[]
}

export type IUser = IAuditAdmin | IJurisdictionAdmin | IAuditBoard

export interface ISupportUser {
  email: string
}

export interface IAuthData {
  user: IUser | null
  supportUser: ISupportUser | null
}

const AuthDataContext = createContext<IAuthData | null>(null)

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const AuthDataProvider = (props: any) => {
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

export const useAuthDataContext = () => useContext(AuthDataContext)

export default AuthDataProvider
