import React, {
  createContext,
  useState,
  useEffect,
  useMemo,
  useContext,
} from 'react'
import { IAuthData, IUserMeta, IErrorResponse } from '../types'
import { api, checkAndToast } from './utilities'

const initialAuthData: IAuthData = { isAuthenticated: null }
export const AuthDataContext = createContext<IAuthData>(initialAuthData)

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const AuthDataProvider = (props: any) => {
  const [authData, setAuthData] = useState<IAuthData>(initialAuthData)

  useEffect(() => {
    ;(async () => {
      const currentAuthData: IUserMeta | IErrorResponse = await api('/auth/me')
      if ('redirect' in currentAuthData || checkAndToast(currentAuthData)) {
        setAuthData(initialAuthData)
      } else if (currentAuthData.type) {
        setAuthData({
          isAuthenticated: true,
          meta: currentAuthData,
        })
      } else {
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
