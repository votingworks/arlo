import React, {
  createContext,
  useState,
  useEffect,
  useMemo,
  useContext,
} from 'react'
import { IAuthData, IUserMeta } from '../types'
import { api } from './utilities'

const initialAuthData: IAuthData = { isAuthenticated: null }
export const AuthDataContext = createContext<IAuthData>(initialAuthData)

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const AuthDataProvider = (props: any) => {
  const [authData, setAuthData] = useState<IAuthData>(initialAuthData)

  useEffect(() => {
    ;(async () => {
      const meta = await api<IUserMeta>('/me')
      if (!meta) {
        setAuthData({ isAuthenticated: false })
        return
      }
      setAuthData({
        isAuthenticated: true,
        meta,
      })
    })()
  }, [])

  // const onLogout = () => setAuthData(initialAuthData)

  // const onLogin = (newAuthData: IAuthData) => setAuthData(newAuthData)

  const authDataValue = useMemo(() => ({ ...authData }), [authData])

  return <AuthDataContext.Provider value={authDataValue} {...props} />
}

export const useAuthDataContext = () => useContext(AuthDataContext)

export default AuthDataProvider
