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
      try {
        const meta: IUserMeta = await api('/me')
        setAuthData({
          isAuthenticated: true,
          meta,
        })
      } catch (err) {
        setAuthData({ isAuthenticated: false })
      }
    })()
  }, [])

  // const onLogout = () => setAuthData(initialAuthData)

  // const onLogin = (newAuthData: IAuthData) => setAuthData(newAuthData)

  const authDataValue = useMemo(() => ({ ...authData }), [authData])

  return <AuthDataContext.Provider value={authDataValue} {...props} />
}

export const useAuthDataContext = () => useContext(AuthDataContext)

export default AuthDataProvider
