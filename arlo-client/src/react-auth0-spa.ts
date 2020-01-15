// src/react-auth0-spa.js
import React, { useState, useEffect, useContext } from 'react'
import createAuth0Client from '@auth0/auth0-spa-js'
import Auth0Client from "@auth0/auth0-spa-js/dist/typings/Auth0Client"

interface IAuth0Context {
  isAuthenticated: boolean;
  user: any;
  loading: boolean;
  popupOpen: boolean;
  loginWithPopup(options: PopupLoginOptions): Promise<void>;
  handleRedirectCallback(): Promise<RedirectLoginResult>;
  getIdTokenClaims(o?: getIdTokenClaimsOptions): Promise<IdToken>;
  loginWithRedirect(o: RedirectLoginOptions): Promise<void>;
  getTokenSilently(o?: GetTokenSilentlyOptions): Promise<string | undefined>;
  getTokenWithPopup(o?: GetTokenWithPopupOptions): Promise<string | undefined>;
  logout(o?: LogoutOptions): void;
}
interface IAuth0ProviderOptions {
  children: React.ReactElement;
  onRedirectCallback?(result: RedirectLoginResult): void;
}

const DEFAULT_REDIRECT_CALLBACK = () =>
  window.history.replaceState({}, document.title, window.location.pathname)

export const Auth0Context = React.createContext<IAuth0Context | null>(null)
export const useAuth0 = () => useContext(Auth0Context)
//const { Provider } = Auth0Context
export const Auth0Provider = ({
  children,
  onRedirectCallback = DEFAULT_REDIRECT_CALLBACK,
  ...initOptions
}: IAuth0ProviderOptions & Auth0ClientOptions): React.FC<IAuth0ProviderOptions & Auth0ClientOptions> => {
  const [isAuthenticated, setIsAuthenticated] = useState()
  const [user, setUser] = useState()
  const [auth0Client, setAuth0] = useState<Auth0Client>()
  const [loading, setLoading] = useState(true)
  const [popupOpen, setPopupOpen] = useState(false)
  
  useEffect(() => {
    const initAuth0 = async () => {
      const auth0FromHook = await createAuth0Client(initOptions)
      setAuth0(auth0FromHook)
      
      if (window.location.search.includes('code=')) {
        const { appState } = await auth0FromHook.handleRedirectCallback()
        onRedirectCallback(appState)
      }
      
      const isAuthenticated = await auth0FromHook.isAuthenticated()
      
      setIsAuthenticated(isAuthenticated)
      
      if (isAuthenticated) {
        const user = await auth0FromHook.getUser()
        setUser(user)
      }
      
      setLoading(false)
    }
    initAuth0()
    // eslint-disable-next-line
  }, [])
  
  const loginWithPopup = async (params: PopupLoginOptions) => {
    setPopupOpen(true)
    try {
      await auth0Client!.loginWithPopup(params)
    } catch (error) {
      //eslint-disable-next-line
      console.error(error)
    } finally {
      setPopupOpen(false)
    }
    const user = await auth0Client!.getUser()
    setUser(user)
    setIsAuthenticated(true)
  }
  
  const handleRedirectCallback = async () => {
    setLoading(true)
    const result = await auth0Client!.handleRedirectCallback()
    const user = await auth0Client!.getUser()
    setLoading(false)
    setIsAuthenticated(true)
    setUser(user)
    return result
  }
  return (
    <Auth0Context.Provider
      value={{
        isAuthenticated,
        user,
        loading,
        popupOpen,
        loginWithPopup,
        handleRedirectCallback,
        getIdTokenClaims: (p: getIdTokenClaimsOptions | undefined) => auth0Client!.getIdTokenClaims(p),
        loginWithRedirect: (p: RedirectLoginOptions) => auth0Client!.loginWithRedirect(p),
        getTokenSilently: (p: GetTokenSilentlyOptions | undefined) => auth0Client!.getTokenSilently(p),
        getTokenWithPopup: (p: GetTokenWithPopupOptions | undefined) => auth0Client!.getTokenWithPopup(p),
        logout: (p: LogoutOptions | undefined) => auth0Client!.logout(p)
      }}
    >
      {children}
    </Auth0Context.Provider>
  )
}
